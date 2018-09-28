from __future__ import print_function

import difflib
import re
import sys

from collections import defaultdict, namedtuple

from tdda.rexpy import extract

LINE_NUMBER_RE = re.compile(r'^@@\s+\-(\d+)(,\d+)?\s+\+(\d+)(,\d+)?\s+@@$')
TOGETHER = True
GROUP_RE = False

Pair = namedtuple('Pair',
                  'left_content right_content left_line_num right_line_num')


def diffs(left_path, right_path):
    with open(left_path) as f:
        left_lines = f.readlines()
    with open(right_path) as f:
        right_lines = f.readlines()
    return difflib.unified_diff(left_lines, right_lines, left_path, right_path)


def find_diff_lines(left_path, right_path):
    pairs, L, R = [], [], []
    left_num = right_num = None
    for i, line in enumerate(diffs(left_path, right_path)):
        if i < 2:
            continue
        line_source = line[:1]
        if line_source == '@':
            if L or R:
                add_pairs(pairs, L, R, left_num, right_num)
                L, R = [], []
            m = re.match(LINE_NUMBER_RE, line)
            if not m:
                raise Exception('Bad line %s' % line[:-1])
            left_num, right_num = int(m.group(1)), int(m.group(3))
        elif line_source == '-':  # left
            L.append(line[1:-1])
        elif line_source == '+':  # right
            R.append(line[1:-1])
        elif line_source != ' ':  # common line
            print('DID NOT EXPECT THIS', prev_source, line_source)
    if L or R:
        add_pairs(pairs, L, R, left_num, right_num)

    return pairs


def show_diff_rexes(left_path, right_path, together=TOGETHER, group=GROUP_RE):
    pairs = find_diff_lines(left_path, right_path)
    if pairs:
        if together:
            lefts = [p[0] for p in pairs if p[0]]
            rights = [p[1] for p in pairs if p[1]]
            rexes = extract(lefts + rights, tag=group)
            print('Patterns:')
            for r in rexes:
                print(r)
        else:
            rexes = defaultdict(list)
            fails = []
            for p in pairs:
                print(p.left_content, end='')
                print(p.right_content, end='')
                patterns = extract([p.left_content, p.right_content],
                                   tag=group)
                if len(patterns) == 1:
                    rex = patterns.pop()
                    print('/%s' % rex)
                    rexes[rex].append((p.left_line_num, p.right_line_num))
                else:
                    print('*** Could not find RE.')
                    fails.append((left, right))
                print()
            print('%d pattern%s for %d line pair%s'
                  % (len(rexes), 's' if len(rexes) != 1 else '',
                     len(pairs), 's' if len(pairs) != 1 else ''))
            for r, lines in sorted(rexes.items()):
                print(' ', r)
                print('     ', lines)
            if fails:
                print()
            print('%d pair%s of lines failed:'
                  % (len(fails), 's' if len(fails) != 1 else ''))
            for left, right in fails:
                print(left)
                print(right)
                print()
    else:
        print('(no diffs)')


def add_pairs(pairs, L, R, left_num, right_num):
    if L or R:
        for i in range(max(len(L), len(R))):
            pairs.append(Pair(L[i] if i < len(L) else '',
                              R[i] if i < len(R) else '',
                              (left_num + i) if i < len(L) else 0,
                              (right_num + i) if i < len(R) else 0))


if __name__ == '__main__':
    show_diff_rexes(sys.argv[1], sys.argv[2])
    # r = find_diff_lines(sys.argv[1], sys.argv[2])
    # print('PAIRS')
    # print(r.pairs)
    # print('\nLEFT')
    # print(r.left)
    # print('\nRIGHT')
    # print(r.right)