#!/usr/bin/env python3

import sys

abc = "abcdefghijklmnopqrstuvwxyz"
num = "0123456789"
punc = ".:;,-|~!@#$%^&*/+=?`<>'"

def lex(chars):
    status = None
    buf = ""
    for c in chars + "\0":
        print ("  ", status, buf)

        if status is None:
            pass
        elif status == "string":
            buf += c
            if c == "\\":
                status = "string_escape"
            elif c == '"':
                yield "TOK", buf, status
                status, buf = None, ""
            continue
        elif status == "string_escape":
            if c in ('nr"\\'):
                buf += c
                status = "string"
                continue
            raise Exception(f"can't escape this character in string: {c}")
        elif status in ("symbol", "substitution"):
            if c.lower() in abc or c in num or c == "_":
                buf += c
                continue
            yield "TOK", buf, status
            status, buf = None, ""
        elif status == "num":
            if c in num or c == "_":
                buf += c
                continue
            yield "TOK", buf, status
            status, buf = None, ""
        elif status == "punc":
            if c in punc:
                buf += c
                continue
            yield "TOK", buf, status
            status, buf = None, ""
        elif status in ("lparen", "rparen"):
            yield "TOK", buf, status
            status, buf = None, ""

        if c in " \n\t":
            continue

        buf += c
        if c == "\\":
            # TODO symbol_start. Symbol can only start with abc
            status = "symbol"
        elif c == '"':
            status = "string"
        elif c.lower() in abc:
            status = "substitution"
        elif c in num or c == "_":
            status = "num"
        elif c in punc:
            status = "punc"
        elif c in "([{":
            status = "lparen"
        elif c in ")]}":
            status = "rparen"

if __name__ == "__main__":
    inp = sys.argv[1]
    for TOK, buf, status in lex(inp):
        print(TOK, buf, status)
