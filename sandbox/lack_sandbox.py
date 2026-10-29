#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
匮乏沙盘 —— 拿数据验「缺口」，不写鸡汤。

跑法：
    python sandbox/lack_sandbox.py
退出码：0 全过，1 有失败。

核心对照：
  全知系统（覆盖全部段，无缺口）→ 不会猜
  压缩系统（只带走结论，有缺口）→ 缺口逼它猜 → 猜错被推翻 → 修好

极端环境 = 零缺口 / 全缺口 / 缺口命中率 0 / 可撤回 vs 不可逆。
"""

import sys
import time

results = []


def case(name):
    def deco(fn):
        try:
            fn()
            results.append((name, 'PASS', ''))
        except AssertionError as e:
            results.append((name, 'FAIL', str(e)[:300]))
        except Exception as e:
            results.append((name, 'FAIL', f'{type(e).__name__}: {e}'[:300]))
        return fn
    return deco


def assert_eq(got, want, label=''):
    if got != want:
        raise AssertionError(f'{label}: 期望 {want!r}，实际 {got!r}')


def assert_true(cond, msg=''):
    if not cond:
        raise AssertionError(msg or '断言失败')


class Mind:
    """一个只看得到「结论」的系统：原文分段，但每次只带走一部分。"""

    def __init__(self, segments):
        self.segments = segments          # 原文段（它不知道，或只听说过结论）
        self.covered = set()              # 它已经带走的段号
        self.hypotheses = []              # 它猜过的
        self.falsified = 0                # 被推翻的次数
        self.fixed = []                   # 修好的段

    def cover(self, segs):
        self.covered |= set(segs)

    def gap(self):
        """缺口 = 处理不了（没带走）的那些段。"""
        return [i for i in range(1, len(self.segments) + 1) if i not in self.covered]

    def guess(self, seg, truth=None):
        """在缺口上猜：先猜，再被证伪或证实。返回 True=猜对。"""
        self.hypotheses.append(seg)
        if truth is None:
            return False
        ok = (truth == seg)
        if not ok:
            self.falsified += 1
        return ok

    def fill(self, seg):
        self.covered.add(seg)
        self.fixed.append(seg)


def make_segments(n):
    return ['第%d段原文' % i for i in range(1, n + 1)]


# ---------------------------------------------------------------- 组一：缺口是「猜」的开关

@case('1 无缺口系统（全知）：覆盖全部段 → 缺口=0 → 不会猜')
def t1():
    m = Mind(make_segments(30))
    m.cover(range(1, 31))
    assert_eq(m.gap(), [], '全知系统还有缺口')
    assert_eq(len(m.hypotheses), 0, '全知系统居然在猜')


@case('2 有缺口系统（压缩）：只带走结论 → 缺口>0 → 去猜')
def t2():
    m = Mind(make_segments(30))
    m.cover([1, 2, 3])          # 只带走了开头三段当"结论"
    gap = m.gap()
    assert_eq(len(gap), 27, '缺口数')
    # 它在缺口上猜一次
    target = gap[0]
    m.guess(target, truth=target)
    assert_eq(len(m.hypotheses), 1, '有缺口却没猜')


@case('3 猜错被推翻：猜了错的段 → 被推翻 → 再猜对的')
def t3():
    m = Mind(make_segments(10))
    m.cover([1])
    gap = m.gap()               # 2..10
    wrong = gap[0]              # 猜 2
    truth = gap[1]              # 真缺口在 3
    assert_true(m.guess(wrong, truth=truth) is False, '猜错却没被推翻')
    assert_eq(m.falsified, 1, '推翻计数')
    assert_true(m.guess(truth, truth=truth) is True, '猜对没确认')
    m.fill(truth)
    assert_eq(len(m.gap()), 8, '修好后缺口数')


# ---------------------------------------------------------------- 组二：缺口 = 需要猜的次数

@case('4 缺口大小决定要猜多少次：200 段只带 1 段 → 199 次')
def t4():
    m = Mind(make_segments(200))
    m.cover([1])
    assert_eq(len(m.gap()), 199, '缺口数')


@case('5 零缺口 vs 全缺口：两个极端')
def t5():
    full = Mind(make_segments(50))
    full.cover(range(1, 51))
    empty = Mind(make_segments(50))
    assert_eq(len(full.gap()), 0, '零缺口')
    assert_eq(len(empty.gap()), 50, '全缺口')


# ---------------------------------------------------------------- 组三：主动 vs 被迫

@case('6 主动匮乏：可撤回的窄化——窄化后能撤回，系统复原')
def t6():
    m = Mind(make_segments(20))
    m.cover(range(1, 21))       # 满
    before = len(m.gap())
    narrowed = set(list(m.covered)[:10])   # 主动窄化：只保留一半
    m.covered = narrowed
    assert_eq(len(m.gap()), 10, '窄化后缺口')
    m.covered = set(range(1, 21))          # 撤回，恢复
    assert_eq(len(m.gap()), before, '撤回后没复原')


@case('7 被迫匮乏：不可逆降格——砍掉的能力回不来')
def t7():
    m = Mind(make_segments(20))
    m.cover(range(1, 21))
    m.covered = set()           # 全砍，相当于"能力没了"
    assert_eq(len(m.gap()), 20, '砍完缺口')
    # 试图恢复：只恢复 1 段，剩下的回不来（模拟不可逆）
    m.fill(1)
    assert_eq(len(m.gap()), 19, '不可逆降格居然复原了')


# ---------------------------------------------------------------- 组四：极端环境

@case('8 极端·缺口命中率 0：猜的全是错段，被推翻 100 次也不崩')
def t8():
    m = Mind(make_segments(100))
    m.cover(range(1, 99))       # 缺口 99,100
    for _ in range(100):
        wrong = 1               # 一直猜已覆盖的段（错）
        m.guess(wrong, truth=99)
    assert_eq(m.falsified, 100, '推翻计数')


@case('9 极端·规模：5000 段 + 4000 次猜，速度可控')
def t9():
    t0 = time.perf_counter()
    m = Mind(make_segments(5000))
    m.cover(range(1, 1001))     # 缺口 1001..5000
    for i in range(4000):
        m.guess(1001 + i, truth=1001 + i)
    dt = time.perf_counter() - t0
    assert_true(dt < 20, '太慢：%.2fs' % dt)
    results.append(('   · 5000 段 + 4000 次猜耗时', 'INFO', '%.3fs' % dt))


@case('10 极端·满缺口：系统没有任何"结论"，全在猜——不崩、计数对')
def t10():
    m = Mind(make_segments(300))
    gap = m.gap()
    assert_eq(len(gap), 300, '全缺口')
    for seg in gap[:300]:
        m.guess(seg, truth=seg)
    assert_eq(len(m.hypotheses), 300, '猜的次数')


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    print('匮乏沙盘 · 10 个场景\n')
    fails = 0
    for name, status, detail in results:
        mark = {'PASS': 'PASS', 'FAIL': 'FAIL', 'INFO': 'INFO '}[status]
        print(f'[{mark}] {name}')
        if status == 'FAIL':
            print(f'        {detail}')
            fails += 1
    print('\n—— %d 个场景，%d 失败 ——' % (len(results) - 1, fails))
    return 0 if fails == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
