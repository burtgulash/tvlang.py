#!/usr/bin/env python3

import sys

import lex
import parse
from tvl_types import Value, Token, NIL

TU = 0

def bind(a, b, env):
    if isinstance(a, Value) and a.T == "cons":
        aa, ab = a.value
        assert ab.T == "num"
        if ab.value > 0:
            return aa
    return b

def right(a, b, env):
    return b

def bool_and(a, b, env):
    assert a.T == "num"
    if a.value <= 0:
        return Value("num", 0)
    return b

def bool_or(a, b, env):
    assert a.T == "num"
    if a.value <= 0:
        return b
    return Value("num", 1)

def cons(a, b, env):
    return Value("cons", [a, b])

def revcons(a, b, env):
    return Value("cons", [b, a])

def println(a, b, env):
    print("println", a)
    return a

def sleep(a, b, env):
    import time
    time.sleep(1)
    return a

def plus(a, b, env):
    assert a.T == b.T == "num"
    return Value("num", a.value + b.value)

def equals(a, b, env):
    assert a.T == b.T == "num"
    return Value("num", int(a.value == b.value))

def minus(a, b, env):
    assert a.T == b.T == "num"
    return Value("num", a.value - b.value)

def assign(a, b, env):
    if b.T == "cons" and a.T == "cons":
        assign(a.value[0], b.value[0], env)
        assign(a.value[1], b.value[1], env)
    elif b.T == "sym":
        env[1][b.value] = a
    else:
        raise Exception(f"ASSIGN expecting b.T == 'sym'. Got '{b.T}'")
    return a


def mkfn(a, b, env, func_T="func"):
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

    return Value(func_T, (env, x, y, body))


def mkfn_arrow(a, b, env, func_T="func"):
    body = b
    if a.T == "cons":
        x, y = a.value[0], a.value[1]
        assert x.T == y.T == "sym"
        x, y = x.value, y.value
    elif a.T == "sym":
        x, y = a.value, None
    else:
        raise Exception("Can't construct function. Params are either cons or a sym")

    return Value(func_T, (env, x, y, body))

FNS = {
    "println": Value("builtin", println),
    "sleep": Value("builtin", sleep),
    "==": Value("builtin", equals),
    "+": Value("builtin", plus),
    "-": Value("builtin", minus),
    "and": Value("special", bool_and),
    "or": Value("special", bool_or),
    "then": Value("builtin", revcons),
    ".": Value("builtin", cons),
    ":": Value("builtin", cons),
    "|": Value("special", bind),
    ";": Value("builtin", right),
    "as": Value("builtin", assign),
    #"fn": Value("special", lambda a, b, env: mkfn(a, b, env, func_T="func")),
    "->": Value("special", lambda a, b, env: mkfn_arrow(a, b, env, func_T="func")),
    "=>": Value("special", lambda a, b, env: mkfn_arrow(a, b, env, func_T="special_func")),
    #"sfn": Value("special", lambda a, b, env: mkfn(a, b, env, func_T="special_func")),
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
                if frame[1].T in ("special", "special_func", "label", "return", "cont", "num"):
                    frame[2] = x[2]

                    # TODO it will be popped in a second
                    # frame[3] = skip
                    # skip = 4
                else:
                    frame[3] = skip
                    skip, x = 0, x[2]
                    continue



            L, H, R, _, _, env = frame
            #L, H, R, _, _, env = st.pop()
            st.pop()

            fn = H

            if fn.T == "nil":
                assert fn is NIL
                skip, x = 0, NIL
                continue
            elif fn.T == "num":
                if fn.value > 0:
                    y = L
                else:
                    y = R
                skip, x = 0, y
                continue
            elif fn.T in ("builtin", "special"):
                y = fn.value(L, R, env)

                skip, x = 0, y
                continue
            elif fn.T in ("func", "special_func"):
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

                # Tail call optimization. Pop one level of CStack when only 1 frame in the current one
                # It assumes that this stack frame is the one where continuation is called.
                #
                # TODO add assertion about this?
                # Answer: there doesn't need to be the assertion, because fn.T
                # is checked to be "cont", so this frame has to be the cont
                # frame
                if len(st) == 1 and parst:
                    parst, st, label = parst

                for k_st, k_label in fn.value:
                    k_st = [f.copy() for f in k_st]
                    parst, st, label = (parst, st, label), k_st, k_label

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
        if x.T == "cont":
            return "(cont)"
        return str(x.value)
    elif isinstance(x, Token):
        return str(x.value)
        # TODO uncomment for more verbose print
        #return f"{x.value}::TOK({x.T})"
    else:
        assert isinstance(x, list)
        return " ".join(map(x2str, x))



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

    #print()
    #print("EVAL1")
    #y = eval1(tree, env)
    #print("EVAL1", x2str(y))
