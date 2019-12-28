#!/usr/bin/env python3
import sys
import lex

def pparse(toks):
    tok = next(toks)
    if tok[2] == "rparen":
        x, end = tok[1], True
    elif tok[2] == "lparen":
        x, end = parse(toks, ")"), None
    else:
        x, end = tok[1], None
    return x, end

def parse(toks, expected_end):
    L, end = pparse(toks)
    if end and L == expected_end:
        return "()"

    while True:
        H, end = pparse(toks)
        if end and H == expected_end:
            break

        R, end = pparse(toks)
        assert not end
        L = [L, H, R]

    return L

if __name__ == "__main__":
    s = sys.argv[1]
    toks = lex.lex(s)
    tree = parse(toks, "EOF")
    print(tree)
