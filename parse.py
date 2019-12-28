#!/usr/bin/env python3
import sys
import lex

def pp(x):
    if isinstance(x, list):
        return "({})".format("".join(map(pp, x)))
    else:
        return x[1]

def flush_til(buf, out_q, lvl):
    R = buf.pop()
    while out_q:
        if out_q[-1][1] > lvl:
            break
        H = out_q.pop()[0]
        L = buf.pop()
        R = [L, H, R]
    return R

def pparse(toks):
    tok = next(toks)
    if tok[2] == "rparen":
        x, end = tok, True
    elif tok[2] == "lparen":
        x, end = parse(toks, ")"), None
    else:
        x, end = tok, None
    return x, end

def parse(toks, expected_end):
    buf, out_q = [], []

    L, end = pparse(toks)
    if end and L[1] == expected_end:
        return "()"

    buf.append(L)

    while True:
        H, end = pparse(toks)
        if end and H[1] == expected_end:
            break

        R, end = pparse(toks)
        assert not end

        right_assoc = 0
        op = H[1]
        if op == ';':
            lvl = 4
        elif op == "|":
            lvl = 3
            right_assoc = 1
        elif op == ",":
            lvl = 2
        elif op == ".":
            lvl = 1
        elif op == ":":
            lvl = 0
            right_assoc = 1
        else:
            lvl = 1

        buf.append(flush_til(buf, out_q, lvl - right_assoc))
        buf.append(R)
        out_q.append((H, lvl))

    return flush_til(buf, out_q, 999)

if __name__ == "__main__":
    s = sys.argv[1]
    toks = lex.lex(s)
    tree = parse(toks, "EOF")
    print(pp(tree))
