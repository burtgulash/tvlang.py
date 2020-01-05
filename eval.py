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

def rettree(a, b):
    return [Token("num", 100), Token("punc", "."), Token("num", 200)]

def assign(a, b, env):
    #print(repr(b))
    assert b.T == "sym"
    env[1][b.value] = a
    #print("ENV", env[1])
    return a

FNS = {
    "rettree": Value("builtin", rettree),
    ".": Value("builtin", cons),
    ":": Value("builtin", cons),
    ",": Value("builtin", rcons),
    "|": Value("builtin", right),
    "as": Value("special", assign),
    "return": Value("return", "return"),
    "label": Value("label", "label"),
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
    while True:
        if isinstance(x, Value):
            if x.T == "var":
                y = env_lookup(env, x.value)
            else:
                y = x
            break
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
            break
        elif isinstance(x, list):
            L = eval1(x[0], env)
            H = eval1(x[1], env)
            R = eval1(x[2], env)

            fn = H
            if fn.T == "builtin":
                y = fn.value(L, R)
            elif fn.T == "special":
                y = fn.value(L, R, env)
            else:
                raise Exception(f"Can't process this fn type: {fn.value}::{fn.T}")
            x = y
        else:
            raise AssertionError("eval: Can only process list or TUPLE")
    return y

def eval2(x, env):
    parst, st, label = None, [], "root"
    skip = 0

    while True:
        ins = None
        #print("X", x)
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
            #print("ST", x2str(x), [(f[3], x2str(f[4])) for f in st])

# TODO for Tail Call Optimization
#            if skip == -1:
#                frame = [None, None, None, skip, x, env]
#                st.append(frame)
#                skip = 0

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
                if frame[1].T in ["builtin", "special"]:
                    frame[3] = skip
                    skip, x = 0, x[2]
                    continue
                else:
                    frame[2] = x[2]


            L, H, R, _, _, env = frame
            #L, H, R, _, _, env = st.pop()
            st.pop()

            fn = H
            if fn.T == "builtin":
                y = fn.value(L, R)
            elif fn.T == "special":
                y = fn.value(L, R, env)
            elif fn.T == "func":
                fn_body, fn_env = fn.value
                y = fn_body
                if True:
                    # TODO TCO
                    env = (fn_env, {"fuu": Value("num", -1)})
            elif fn.T == "cont":
                for k_st, k_label in fn.value:
                    parst, st, label = (parst, st, label), k_st.copy(), k_label

                skip, x = 0, L
                continue
            elif fn.T == "return":
                assert L.T == "sym"
                until_label = L.value

                ks = []
                while True:
                    ks.append((st, label))
                    if not parst:
                        raise Exception(f"Couldn't return to label '{until_label}'")
                    cur_label = label
                    parst, st, label = parst
                    if cur_label == until_label:
                        break
                ks.reverse()

                env = (env, {"K": Value("cont", ks)})
                skip, x = 0, R
                continue
            elif fn.T == "label":
                assert L.T == "sym"
                parst, st, label = (parst, st, label), [], L.value

                skip, x = 0, R
                continue
            else:
                raise Exception(f"Can't process non function: {fn.value}::{fn.T}")

            skip, x = 0, y
            continue
        else:
            raise AssertionError("eval: Can only process TVL types")

        while not st and parst:
            parst, st, label = parst

        if st:
            frame = st[-1]
            skip, x, env = frame[3], frame[4], frame[5]
            frame[skip] = y
            skip += 1
            continue

        return y


def x2str(x):
    if isinstance(x, Value):
        if x.T == "cons":
            return "(" + ".".join(map(x2str, x.value)) + ")"
        return str(x.value)
    elif isinstance(x, Token):
        return str(x.value)
        # TODO uncomment for more verbose print
        #return f"{x.value}::TOK({x.T})"
    else:
        assert isinstance(x, list)
        return "".join(map(x2str, x))



if __name__ == "__main__":
    s = sys.argv[1]
    toks = lex.lex(s)
    tree = parse.parse(toks, "EOF")

    env = (None, {
        **FNS,
        "FOO": Value("func", (Value("num", 1000), (None, {}))),
    })

    print("EVAL2")
    y = eval2(tree, env)
    print("EVAL2", x2str(y))

    #print()
    #print("EVAL1")
    #y = eval1(tree, env)
    #print("EVAL1", x2str(y))
