#!/usr/bin/env python3

import sys

import lex
import parse
from tvl_types import Value, Token

def right(a, b):
    return b

def cons(a, b):
    return Value("cons", [a, b])

def rcons(a, b):
    return Value("cons", [b, a])

def assign(a, b, env):
    #print(repr(b))
    assert b.T == "sym"
    env[1][b.value] = a
    #print("ENV", env[1])
    return a

FNS = {
    ".": Value("func", cons),
    ":": Value("func", cons),
    ",": Value("func", rcons),
    "|": Value("func", right),
    "as": Value("special", assign),
}


def env_lookup(env, key):
    while True:
        parent, env_dict = env
        if key in env_dict:
            return env_dict[key]
        if not parent:
            raise Exception(f"Can't env lookup: {key}")
        env = parent


def eval1(x, env):
    if isinstance(x, Value):
        if x.T == "var":
            y = env_lookup(env, x.value)
        else:
            y = x
    elif isinstance(x, Token):
        if x.T == "num":
            y = Value("num", int(x.value))
        elif x.T == "symbol":
            y = Value("sym", x.value[1:])
        elif x.T in ("punc", "var"):
            x = Value("var", x.value)
            y = eval1(x, env)
        else:
            raise Exception("Can't parse this")
    elif isinstance(x, list):
        L = eval1(x[0], env)
        H = eval1(x[1], env)
        R = eval1(x[2], env)

        fn = H
        if fn.T == "func":
            y = fn.value(L, R)
        elif fn.T == "special":
            y = fn.value(L, R, env)
        else:
            raise Exception(f"Can't process non function: {fn.value}::{fn.T}")
    else:
        raise AssertionError("eval: Can only process list or TUPLE")
    return y

def eval2(x, env):
    st = []
    skip = 0

    while True:
        if isinstance(x, Value):
            if x.T == "var":
                y = env_lookup(env, x.value)
            else:
                y = x
        elif isinstance(x, Token):
            if x.T == "num":
                y = Value("num", int(x.value))
            elif x.T == "symbol":
                y = Value("sym", x.value[1:])
            elif x.T in ("punc", "var"):
                x = Value("var", x.value)
                continue
            else:
                raise Exception("Can't parse this")
        elif isinstance(x, list):
            #print("ST", [f[1:] for f in st])
            if skip == 0:
                frame = [None, None, None, skip, x, env]
                st.append(frame)
                skip, x = 0, x[0]
                continue
            if skip == 1:
                frame[3] = skip
                skip, x = 0, x[1]
                continue
            if skip == 2:
                frame[3] = skip
                skip, x = 0, x[2]
                continue

            L, H, R, _, _, env = st.pop()

            fn = H
            if fn.T == "func":
                y = fn.value(L, R)
            elif fn.T == "special":
                y = fn.value(L, R, env)
            else:
                raise Exception(f"Can't process non function: {fn.value}::{fn.T}")
        else:
            raise AssertionError("eval: Can only process TVL types")

        if st:
            frame = st[-1]
            skip, x = frame[3], frame[4]
            frame[skip] = y
            skip += 1
        else:
            return y


def x2str(x):
    if isinstance(x, Value):
        if x.T == "cons":
            return "(" + ".".join(map(x2str, x.value)) + ")"
        return str(x.value)
    elif isinstance(x, Token):
        return f"{x.value}::TOK({x.T})"
    else:
        assert isinstance(x, list)
        return "".join(map(x2str, x))



if __name__ == "__main__":
    s = sys.argv[1]
    toks = lex.lex(s)
    tree = parse.parse(toks, "EOF")

    env = (None, {
        **FNS,
    })

    print("EVAL2")
    y = eval2(tree, env)
    print("EVAL2", x2str(y))

    print()
    print("EVAL1")
    y = eval1(tree, env)
    print("EVAL1", x2str(y))
