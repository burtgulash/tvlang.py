#!/usr/bin/env python3

import sys

import lex
import parse
from tvl_types import Value, Token

def right(a, b, env):
    return b

def cons(a, b, env):
    return Value("cons", [a, b])

def rcons(a, b, env):
    return Value("cons", [b, a])

def rettree(a, b, env):
    return [Token("num", 100), Token("punc", "."), Token("num", 200)]

def assign(a, b, env):
    assert b.T == "sym"
    env[1][b.value] = a
    #print("ENV", env[1])
    return a


def mkfn(a, b, env):
    assert isinstance(a, Value) and a.T == "cons"
    assert isinstance(a.value[0], Value)

    L = a.value[0]
    if L.T == "cons":
        x, y = L.value[0], L.value[1]
        assert x.T == y.T == "sym"
        x, y = x.value, y.value
    elif L.T == "sym":
        x, y = a.value, None
    else:
        raise Exception("Can't construct function. Params are either cons or a sym")
    body = a.value[1]

    return Value("func", (env, x, y, body))

FNS = {
    "rettree": Value("builtin", rettree),
    ".": Value("builtin", cons),
    ":": Value("builtin", cons),
    ":::": Value("special", cons),
    ",": Value("builtin", rcons),
    "|": Value("builtin", right),
    "as": Value("builtin", assign),
    "mkfn": Value("special", mkfn),
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
                y = fn.value(L, R, env)
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
            if skip == 0:
                frame = [None, None, None, skip, x, env]
                st.append(frame)
                skip = 1
            if skip == 1:
                frame[3] = skip
                skip, x = 0, x[0]
                continue
            if skip == 2:
                frame[3] = skip
                skip, x = 0, x[1]
                continue

            if skip == 3:
                if frame[1].T in ("special", "label", "return", "cont"):
                    frame[2] = x[2]
                else:
                    frame[3] = skip
                    skip, x = 0, x[2]
                    continue


            L, H, R, _, _, env = frame
            #L, H, R, _, _, env = st.pop()
            st.pop()

            fn = H
            if fn.T in ("builtin", "special"):
                y = fn.value(L, R, env)

                skip, x = 0, y
                continue
            elif fn.T == "func":
                fn_env, x_name, y_name, fn_body = fn.value

                if "_F" in env and env["_F"] is fn:
                    # Tail Call Optimization
                    skip, x = 1, fn_body
                else:
                    new_env = {"_F": fn, x_name: L}
                    if y_name is not None:
                        new_env[y_name] = R
                    env = (fn_env, new_env)
                    skip, x = 0, fn_body

                continue
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

                env = (env, {"_K": Value("cont", ks)})
                skip, x = 0, R
                continue
            elif fn.T == "label":
                assert L.T == "sym"
                parst, st, label = (parst, st, label), [], L.value

                skip, x = 0, R
                continue
            else:
                raise Exception(f"Can't process non function: {fn.value}::{fn.T}")

            assert False
        else:
            raise AssertionError("eval: Can only process TVL types")

        while not st and parst:
            parst, st, label = parst

        if st:
            frame = st[-1]
            skip, x, env = frame[3], frame[4], frame[5]
            position = {
                1: 0,
                2: 1,
                3: 2,
            }[skip]
            frame[position] = y
            #frame[skip - 1] = y
            skip += 1
            continue

        assert isinstance(y, Value)
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
        "FOO": Value("func", ((None, {}), Value("num", 1000))),
    })

    print("EVAL2")
    y = eval2(tree, env)
    print("EVAL2", x2str(y))

    #print()
    #print("EVAL1")
    #y = eval1(tree, env)
    #print("EVAL1", x2str(y))
