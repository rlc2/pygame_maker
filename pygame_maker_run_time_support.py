#!/usr/bin/python -W all

# Author: Ron Lockwood-Childs

# Licensed under LGPL v2.1 (see file COPYING for details)

import random, time

class PyGameMakerCodeBlockRuntimeError(RuntimeError):
    pass

def userfunc_distance(_symbols,start,end):
    return(abs(start - end))

def userfunc_randint(_symbols,max):
    val = 0
    range = max
    if max < 0:
        range = abs(max)
    val = random.randint(0,range)
    if max < 0:
        val = -1 * val
    return(val)

def userfunc_time(_symbols):
    return(int(time.time()))

