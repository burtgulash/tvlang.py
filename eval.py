#!/usr/bin/env python3

import sys

import lex
import parse
from tvl_types import Value, Token

def cons(a, b):
    return Value("cons", [a, b])

fns = {
    ".": cons,
    ":": cons,
    ",": cons,
}

def eval1(x):
    if isinstance(x, list):
        L = eval1(x[0])
        H = eval1(x[1])
        R = eval1(x[2])

        fn = fns[H.value]
        y = fn(L, R)
    elif isinstance(x, Token):
        if x.T == "num":
            y = Value("num", int(x.value))
        elif x.T == "punc":
            y = Value("var", x.value)
        else:
            raise Exception("Can't parse this")
    elif isinstance(x, Value):
        y = x
    else:
        raise AssertionError("eval: Can only process list or TUPLE")
    return y

def eval2(x):
    st = [[x, None, None, None, "return"]]
    skip = 0

    while True:
        if isinstance(x, Value):
            y = x

        elif isinstance(x, Token):
            if x.T == "num":
                y = Value("num", int(x.value))
            elif x.T == "punc":
                y = Value("var", x.value)
            else:
                raise Exception("Can't parse this")

        elif isinstance(x, list):
            #print("ST", [f[1:] for f in st])
            if skip == 0:
                frame = [x, None, None, None, "L"]
                st.append(frame)
                skip, x = 0, x[0]
                continue
            if skip == 1:
                st[-1][4] = "H"
                skip, x = 0, x[1]
                continue
            if skip == 2:
                st[-1][4] = "R"
                skip, x = 0, x[2]
                continue

            _, L, H, R, ins = st.pop()
            #print("FN", L, H, R)

            fn = fns[H.value]
            y = fn(L, R)
        else:
            raise AssertionError("eval: Can only process TVL types")

        ins = st[-1][4]
        x = st[-1][0]
        if ins == "L":
            st[-1][1] = y
            skip = 1
        elif ins == "H":
            st[-1][2] = y
            skip = 2
        elif ins == "R":
            st[-1][3] = y
            skip = 3
        elif ins == "return":
            return y


if __name__ == "__main__":
    s = sys.argv[1]
    toks = lex.lex(s)
    tree = parse.parse(toks, "EOF")

    x = eval2(tree)
    print(repr(x))

    x = eval1(tree)
    print(repr(x))
