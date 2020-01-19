#!/usr/bin/env python3
import sys
import lex

from tvl_types import Token, Value, NIL

def pp(x):
    if isinstance(x, list):
        return "({})".format(" ".join(map(pp, x)))
    else:
        return x.value

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
    if tok.T == "rparen":
        x, end = tok, True
    elif tok.T == "lparen":
        x, end = parse(toks, ")"), None
    else:
        x, end = tok, None
    return x, end

def parse(toks, expected_end):
    buf, out_q = [], []

    L, end = pparse(toks)
    if end and L.value == expected_end:
        return NIL

    buf.append(L)

    while True:
        H, end = pparse(toks)
        if end and H.value == expected_end:
            break

        R, end = pparse(toks)
        if end:
            raise Exception("can't END on R")

        right_assoc = 0
        if isinstance(H, list):
            lvl = 1
        else:
            assert isinstance(H, Token)
            op = H.value
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
