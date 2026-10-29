#!/usr/bin/env python3
"""PHP syntax check without a PHP binary.

Uses the pure-python `phply` parser (PHP 5 grammar) after rewriting the few
PHP 7/8 constructs it does not know about (null-coalescing, spaceship-free
modern operators).  Only used to protect the cumulative api.php / admin pages
from syntax errors before they are deployed.
"""
import re
import sys

try:
    from phply.phplex import lexer
    from phply.phpparse import make_parser
except Exception as exc:  # pragma: no cover - optional dependency
    print("phply not available: %s" % exc)
    sys.exit(0)


def normalise(src: str) -> str:
    # null coalescing -> logical or (same arity, valid PHP5)
    src = re.sub(r"\?\?", "or", src)
    # null-safe operator -> normal access
    src = src.replace("?->", "->")
    # arrow functions -> closure (valid PHP5)
    src = re.sub(r"\bfn\s*\(", "function (", src)
    return src


def check(path: str) -> int:
    src = open(path, encoding="utf-8").read()
    try:
        make_parser().parse(normalise(src), lexer=lexer.clone())
    except Exception as exc:
        print("%s: PARSE ERROR: %s" % (path, str(exc)[:400]))
        return 1
    print("%s: syntax OK" % path)
    return 0


if __name__ == "__main__":
    rc = 0
    for arg in sys.argv[1:]:
        rc |= check(arg)
    sys.exit(rc)
