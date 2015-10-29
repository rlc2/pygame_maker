#!/usr/bin/python -W all

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

import random, time, sys

DEFAULT_UNINITIALIZED_VALUE = -sys.maxint - 1

class PyGameMakerCodeBlockRuntimeError(RuntimeError):
    pass

def update_symbol(_symbols, symname, value):
    if symname[0] == "_":
        _symbols["globals"][symname[1:]] = value
    else:
        if symname in _symbols["locals"].keys() or not symname in _symbols["globals"].keys():
            _symbols["locals"][symname] = value
        else:
            _symbols["globals"][symname] = value

def get_symbol(_symbols, symname):
    symval = DEFAULT_UNINITIALIZED_VALUE
    if symname in _symbols["locals"].keys():
        # local variables can override globals
        symval = _symbols["locals"][symname]
    elif symname in _symbols["globals"].keys():
        symval = _symbols["globals"][symname]
    return symval

def userfunc_distance(_symbols,start,end):
    return(abs(start - end))

def userfunc_randint(_symbols,max):
    val = 0
    randrange = max
    if max < 0:
        randrange = abs(max)
    val = random.randint(0,randrange)
    if max < 0:
        val = -1 * val
    return(val)

def userfunc_time(_symbols):
    return(int(time.time()))

