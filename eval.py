#!/usr/bin/env python3

import sys
import lex
import parse

def cons(a, b):
    return "VAL", [a, b], "CONS"

fns = {
    ".": cons,
    ":": cons,
    ",": cons,
}

def evalu(x):
    if isinstance(x, list):
        L = evalu(x[0])
        H = evalu(x[1])
        R = evalu(x[2])

        fn = fns[H[1]]
        x = fn(L, R)
    elif isinstance(x, tuple):
        if x[0] == "TOK":
            if x[2] == "num":
                x = "VAL", int(x[1]), "num"
        elif x[0] == "VAL":
            pass
        else:
            raise AssertionError("eval: Can only be TOK or VAL")
    else:
        raise AssertionError("eval: Can only process list or TUPLE")
    return x

def eval2(x):
    st = [[x, None, None, None, "return"]]
    skip = 0

    while True:
        if isinstance(x, list):
            #print("ST", [f[1:] for f in st])
            if skip == 0:
                frame = [x, None, None, None, "L"]
                st.append(frame)
                x = x[0]
                continue
            if skip == 1:
                st[-1][4] = "H"
                x = x[1]
                continue
            if skip == 2:
                st[-1][4] = "R"
                x = x[2]
                continue

            _, L, H, R, ins = st.pop()
            print("FN", L, H, R)

            fn = fns[H[1]]
            y = fn(L, R)

        elif isinstance(x, tuple):
            if x[0] == "TOK":
                if x[2] == "num":
                    y = "VAL", int(x[1]), "num"
                elif x[2] == "punc":
                    y = "VAL", x[1], "var"
                else:
                    raise Exception("Can't process this type")
            elif x[0] == "VAL":
                y = x
            else:
                raise AssertionError("eval: Can only be TOK or VAL")

        else:
            raise AssertionError("eval: Can only process list or TUPLE")


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
    print(x)
