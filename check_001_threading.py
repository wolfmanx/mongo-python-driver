#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2012, Wolfgang Scherer, <Wolfgang.Scherer at gmx.de>
# Sponsored by WIEDENMANN SEILE GMBH, http://www.wiedenmannseile.de
#
# This file is part of Wiedenmann Utilities.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>,
# or write to Wolfgang Scherer, <Wolfgang.Scherer at gmx.de>
"""\
check_001_threading.py - ::fillme::

======  ====================
usage:  check_001_threading.py [OPTIONS] ::fillme::
or      import check_001_threading
======  ====================

Options
=======

  -q, --quiet           suppress warnings
  -v, --verbose         verbose test output
  -d, --debug=NUM       show debug information

  -t, --test            run doc tests
  -h, --help            display this help message

Module Members
==============
"""

# --------------------------------------------------
# |||:sec:||| CONFIGURATION
# --------------------------------------------------

import sys
# (progn (forward-line 1) (snip-insert-mode "py.b.printf" t) (insert "\n"))
# adapted from http://www.daniweb.com/software-development/python/code/217214
try:
    printf = eval("print") # python 3.0 case
except SyntaxError:
    printf_dict = dict()
    try:
        exec("from __future__ import print_function\nprintf=print", printf_dict)
        printf = printf_dict["printf"] # 2.6 case
    except SyntaxError:
        def printf(*args, **kwd): # 2.4, 2.5, define our own Print function
            fout = kwd.get("file", sys.stdout)
            w = fout.write
            if args:
                w(str(args[0]))
            sep = kwd.get("sep", " ")
            for a in args[1:]:
                w(sep)
                w(str(a))
            w(kwd.get("end", "\n"))
    del printf_dict

# (progn (forward-line 1) (snip-insert-mode "py.b.sformat" t) (insert "\n"))
try:
    ('{0}').format(0)
    def sformat (fmtspec, *args, **kwargs):
        return fmtspec.format(*args, **kwargs)
except AttributeError:
    try:
        import stringformat
        def sformat (fmtspec, *args, **kwargs):
            return stringformat.FormattableString(fmtspec).format(
                *args, **kwargs)
    except ImportError:
        printf('error: stringformat missing. Try `easy_install stringformat`.', file=sys.stderr)

# (progn (forward-line 1) (snip-insert-mode "py.f.isstring" t) (insert "\n"))
def isstring(obj):
    return isinstance(obj, basestring)
try:
    isstring("")
except NameError:
    def isstring(obj):
        return isinstance(obj, str) or isinstance(obj, bytes)

try:
    reduce_ = reduce
    del(reduce_)
except NameError:
    from functools import reduce

import os
import re

dbg_comm = globals()['dbg_comm'] if 'dbg_comm' in globals() else '# '
dbg_twid = globals()['dbg_twid'] if 'dbg_twid' in globals() else 9
dbg_fwid = globals()['dbg_fwid'] if 'dbg_fwid' in globals() else 15

# (progn (forward-line 1) (snip-insert-mode "py.b.logging" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.b.ordereddict" t) (insert "\n"))
try:
    from collections import OrderedDict
except ImportError:
    try:
        from ordereddict import OrderedDict
    except ImportError:
        printf('error: ordereddict missing. Try `easy_install ordereddict`.', file=sys.stderr)
        sys.exit(1)
    import collections
    collections.OrderedDict = OrderedDict

# @:adhoc_run_time:@
#import adhoc                                               # @:adhoc:@

# (progn (forward-line 1) (snip-insert-mode "py.main.pyramid.activate" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.main.project.libdir" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.main.sql.alchemy" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.main.sql.ws" t) (insert "\n"))

# (progn (forward-line 1) (snip-insert-mode "py.b.dbg.setup" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.b.posix" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.b.os.system.sh" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.b.prog.path" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.b.line.loop" t) (insert "\n"))

# --------------------------------------------------
# |||:sec:||| CLASSES
# --------------------------------------------------

# (progn (forward-line 1) (snip-insert-mode "py.c.placeholder.template" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.c.key.hash.ordered.dict" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.c.progress" t) (insert "\n"))
# --------------------------------------------------
# |||:sec:||| PROGRESS
# --------------------------------------------------
import datetime
class Progress:                                            # ||:cls:||
    '''Report progress time and duration.

    prg = Progress()
    prg.step('Hello World')
    prg.stop()
    '''

    def __init__(self, comment='# ', tag_bars = '|'):        # |:mth:|
        now = datetime.datetime.now()
        self.start_ = now
        self.step_ = now
        self.end_ = now
        self.delta_ = now - now
        self.comment = comment
        self.tag_bars = tag_bars
        printf(sformat("{0}{2:^{1}} {4:<{3}s}: [{5!s}]",
                self.comment,
                globals()['dbg_twid'] if 'dbg_twid' in globals() else 9,
                sformat('{0}:TIM:{0}',self.tag_bars),
                globals()['dbg_fwid'] if 'dbg_fwid' in globals() else 15,
                'start', self.start_), file=sys.stderr)

    def step(self, mark='break'):                            # |:mth:|
        now = datetime.datetime.now()
        self.end_ = now
        self.delta_ = (self.end_ - self.step_)
        printf(sformat("{0}{2:^{1}} {4:<{3}s}: [{5!s}] step: [{6}] total: [{7}]",
                self.comment,
                globals()['dbg_twid'] if 'dbg_twid' in globals() else 9,
                sformat('{0}:TIM:{0}',self.tag_bars),
                globals()['dbg_fwid'] if 'dbg_fwid' in globals() else 15,
                mark, self.end_,
                (self.end_ - self.step_),
                (self.end_ - self.start_),
                ), file=sys.stderr)
        self.step_ = now

    def stop(self):                                          # |:mth:|
        self.step('end')

# (progn (forward-line -1) (insert "\n") (snip-insert-mode "py.s.class" t) (backward-symbol-tag 2 "fillme" "::"))

# --------------------------------------------------
# |||:sec:||| FUNCTIONS
# --------------------------------------------------

# (progn (forward-line 1) (snip-insert-mode "py.f.hl" t) (insert "\n"))
hlr = None
def hlcr(title=None, tag='|||' ':CHP:|||', rule_width=50, **kwargs): # ||:fnc:||
    comm = globals()['dbg_comm'] if 'dbg_comm' in globals() else '# '
    dstr = []
    dstr.append(''.join((comm, '-' * rule_width)))
    if title:
        dstr.append(sformat('{0}{2:^{1}} {3!s}',
                comm, globals()['dbg_twid'] if 'dbg_twid' in globals() else 9,
                tag, title))
        dstr.append(''.join((comm, '-' * rule_width)))
    return '\n'.join(dstr)

def hlsr(title=None, tag='||' ':SEC:||', rule_width=35, **kwargs): # |:fnc:|
    return hlcr(title, tag, rule_width)

def hlssr(title=None, tag='|' ':INF:|', rule_width=20, **kwargs): # |:fnc:|
    return hlcr(title, tag, rule_width)

def hlc(*args, **kwargs):                                    # |:fnc:|
    for line in hlcr(*args, **kwargs).splitlines():
        printe(line, **kwargs)

def hls(*args, **kwargs):                                    # |:fnc:|
    for line in hlsr(*args, **kwargs).splitlines():
        printe(line, **kwargs)

def hlss(*args, **kwargs):                                   # |:fnc:|
    for line in hlssr(*args, **kwargs).splitlines():
        printe(line, **kwargs)

def hl(*args, **kwargs):                                     # |:fnc:|
    for line in hlr(*args, **kwargs).splitlines():
        printe(line, **kwargs)

def hl_lvl(level=0):                                         # |:fnc:|
    global hlr
    if level == 0:
        hlr = hlssr
    elif level == 1:
        hlr = hlsr
    else:
        hlr = hlcr

hl_lvl(0)

# (progn (forward-line 1) (snip-insert-mode "py.f.single.quote" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.f.remove.match" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.f.printenv" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.f.uname-s" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.f.printe" t) (insert "\n"))
def printe(*args, **kwargs):                               # ||:fnc:||
    kwargs['file'] = kwargs.get('file', sys.stderr)
    printf(*args, **kwargs)

# (progn (forward-line 1) (snip-insert-mode "py.f.dbg.squeeze" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.f.dbg.indent" t) (insert "\n"))

# (progn (forward-line -1) (insert "\n") (snip-insert-mode "py.s.func" t) (backward-symbol-tag 2 "fillme" "::"))

# --------------------------------------------------
# |||:sec:|||
# --------------------------------------------------

import time
import pickle
import bson
import bson.objectid

from threading import Thread, Lock
import warnings

import pymongo
from check_000_getstate import have_enable_getstate, have_enable_c, have_get_element_state, bson_encode, BSONConfig

bc = BSONConfig()

# make sure, pickle can find these ...
class TO(object):                                          # ||:cls:||
    def __init__(self):                                      # |:mth:|
        self.attr1 = 'string'
        self.attr2 = 55
        self.attr3 = bson.objectid.ObjectId()

class TOG(TO):                                             # ||:cls:||
    def __getstate__(self):                                  # |:mth:|
        state = OrderedDict()
        state.update(sorted(self.__dict__.items()))
        return state

def default_getstate(value):                               # ||:fnc:||
    if not have_enable_getstate or not bc.is_getstate_enabled():
        try:
            dct = value.__getstate__()
            if isinstance(dct, dict):
                return dct
        except AttributeError:
            pass
    return repr(value)
    return bson.default(value)

def default_pickle(value):                                 # ||:fnc:||
    if not have_enable_getstate or not bc.is_getstate_enabled():
        try:
            dct = value.__getstate__()
            if isinstance(dct, dict):
                return dct
        except AttributeError:
            pass
    try:
        return { '_$pickle': pickle.dumps(value) }
    except Exception:
        # (t, e, tb) = sys.exc_info()
        # import traceback
        # printe(''.join(traceback.format_tb(tb)))
        # printf(sformat('{0}: {1}', t.__name__, e))
        # printf(sformat('{0}', type(tb).__name__))
        #printe('OOPS2: ' + str(e))
        return repr(value)
    return bson.default(value)

def unpickle_objects(dct):                                 # ||:fnc:||
    shown1 = False
    shown2 = False
    for key, value in dct.items():
        try:
            dct[key] = pickle.loads(value['_$pickle'])
            continue
        except (TypeError, KeyError):
            pass
        try:
            _class = value['_$class']
            _state = value['_$state']
            if not shown1:
                printe(sformat(
                    "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[ ]{6!s}[",
                    dbg_comm, dbg_twid, dbg_fwid, ':DBG:', '_class/_state', _class, _state))
                shown1 = True
            # |:todo:| dotted_name_resolve
            __class = globals()[_class]
            obj = __class.__new__(__class)
            try:
                obj.__setstate__(_state)
            except AttributeError:
                obj.__dict__.update(_state)
            dct[key] = obj
            continue
        except (TypeError, KeyError):
            pass

def run(parameters, pass_opts):                            # ||:fnc:||
    """Application runner, when called as __main__."""

    # (progn (forward-line 1) (snip-insert-mode "py.bf.sql.ws" t) (insert "\n"))
    # (progn (forward-line 1) (snip-insert-mode "py.bf.file.arg.loop" t) (insert "\n"))

    import datetime

    conn = pymongo.Connection()
    db = conn.pyjsmo
    db.drop_collection('threading')
    coll = db.threading

    printe(sformat(
        "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
        dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'has_c', bson.has_c()))

    if bc.have_enable_getstate:
        bc.enable_getstate(True)

    try:
        bson.enable_threading()
    except AttributeError:
        pass

    try:
        bson.enable_dict()
    except AttributeError:
        pass

    class Context(object):                                 # ||:cls:||
        pass

    context = Context()
    context.lock = Lock()
    context.deltas1 = []
    context.deltas2 = []
    context.thread1 = None
    context.thread2 = None
    context.large = None
    context.small = None
    context.done = False
    context.default = None

    dict_size = 5000                    # |:config:|
#    dict_size = 5

    duration = 10
#    duration = 2

    def setup_simple():                                    # ||:fnc:||
        context.title = 'Simple BSON encoding/decoding thread test'
        context.large = OrderedDict()
        for indx in range(dict_size):
            context.large[str(indx)] = indx
        key = str(0)
        context.small = OrderedDict()
        context.small[key] = context.large[key]
        context.default = None

    def setup_medium():                                    # ||:fnc:||
        context.title = 'Medium BSON encoding/decoding thread test'
        context.large = OrderedDict()
        for indx in range(dict_size):
            context.large[str(indx)] = TOG()
        key = str(0)
        context.small = OrderedDict()
        context.small[key] = context.large[key]
        context.default = default_getstate

    def setup_complex():                                   # ||:fnc:||
        context.title = 'Complex BSON encoding/decoding thread test'
        context.large = OrderedDict()
        for indx in range(dict_size):
            context.large[str(indx)] = TO()
        key = str(0)
        context.small = OrderedDict()
        context.small[key] = context.large[key]
        context.default = default_pickle

    def start_threads():                                   # ||:fnc:||
        del(context.deltas1[:])
        del(context.deltas2[:])
        context.done = False

        context.thread1 = Thread(target=encode_a_little, args=(True, context, context.deltas1))
        context.thread1.daemon = True
        context.thread1.start()

        context.thread2 = Thread(target=encode_a_little, args=(False, context, context.deltas2))
        context.thread2.daemon = True
        context.thread2.start()

    def terminate_threads():                               # ||:fnc:||
        context.done = True
        context.thread1.join()
        context.thread2.join()

    def encode_a_little(with_c, context, deltas):          # ||:fnc:|| thread
        # bson.thread_init()
        _thread_ctx_dbg = True
        _thread_ctx_dbg = False         # |:debug:|
        if _thread_ctx_dbg:
            _thread_ctx = dict()
            _thread_ctx.update(bson._ctx.__dict__)
        try:
            bson.enable_c(with_c)
        except AttributeError:
            pass
        context.lock.acquire()
        printe(bc.status())
        context.lock.release()

        bc.set_enable_getstate()
        bc.set_enable_dict()
        bc.set_enable_wrap(bc.is_c_enabled())
        save_record = OrderedDict(context.small)
        while not context.done:
            try:
                context.lock.acquire()
                if _thread_ctx_dbg:
                    printe(sformat(
                        "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                        dbg_comm, dbg_twid, dbg_fwid, ':DBG:', '_thread_ctx', _thread_ctx))
                start = datetime.datetime.now()
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    result1 = bson_encode(context.large, default=context.default).decode(as_class=OrderedDict)
                result2 = bson_encode({'a': with_c, 'b': bc.is_c_enabled()}).decode(as_class=OrderedDict)
                end = datetime.datetime.now()

                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        result = coll.save(save_record)
                except bson.errors.InvalidDocument:
                    result = None
                printe(sformat(
                    "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                    dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'save', result))

                unpickle_objects(result1)
                printe(result1["0"])
                printe(result2)
                try:
                    printe(bson_encode(object).decode())
                except Exception:
                    (t, e, tb) = sys.exc_info()
                    # import traceback
                    # printe(''.join(traceback.format_tb(tb)))
                    # printf(sformat('{0}: {1}', t.__name__, e))
                    # printf(sformat('{0}', type(tb).__name__))
                    printe(e)
                sys.stdout.flush()
                sys.stderr.flush()
            finally:
                context.lock.release()
            deltas.append(end-start)
            time.sleep(0.200)

    def run_test():                                        # ||:fnc:||
        hl(context.title)
        prg = Progress()
        start_threads()
        time.sleep(duration)
        terminate_threads()
        prg.stop()

        d1 = list(context.deltas1)
        d2 = list(context.deltas2)

        samples = min(len(d1), len(d2))

        printe(sformat(
            "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
            dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'samples', samples))

        if samples > 0:
            cx_sum = reduce(lambda x, y: x + y, d1[:samples])
            py_sum = reduce(lambda x, y: x + y, d2[:samples])
            cx_avg = cx_sum / samples
            py_avg = py_sum / samples
            fac_avg = float(py_avg.microseconds) / float(cx_avg.microseconds)

            printe(sformat(
                "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'cx_sum', cx_sum))
            printe(sformat(
                "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'py_sum', py_sum))
            printe(sformat(
                "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'delta sum', abs(py_sum - cx_sum)))

            printe(sformat(
                "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'cx_avg', cx_avg))
            printe(sformat(
                "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'py_avg', py_avg))
            printe(sformat(
                "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[ ({6:0.2f})",
                dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'delta avg', abs(py_avg - cx_avg), fac_avg))

    setup_simple()
    run_test()

    setup_medium()
    run_test()

    setup_complex()
    run_test()

    # |:here:|
    pass

# --------------------------------------------------
# |||:sec:||| MAIN
# --------------------------------------------------

_quiet = False
_verbose = False
_debug = False

# (progn (forward-line 1) (snip-insert-mode "py.f.setdefaultencoding" t) (insert "\n"))
def setdefaultencoding(encoding=None, quiet=False):
    if encoding is None:
        encoding='utf-8'
    try:
        isinstance('', basestring)
        if not hasattr(sys, '_setdefaultencoding'):
            if not quiet:
                printf('''\
Add this to /etc/python2.x/sitecustomize.py,
or put it in local sitecustomize.py and adjust PYTHONPATH=".:${PYTHONPATH}"::

    try:
        import sys
        setattr(sys, '_setdefaultencoding', getattr(sys, 'setdefaultencoding'))
    except AttributeError:
        pass

Running with reload(sys) hack ...
''', file=sys.stderr)
            reload(sys)
            setattr(sys, '_setdefaultencoding', getattr(sys, 'setdefaultencoding'))
        sys._setdefaultencoding(encoding)
    except NameError:
        # python3 already has utf-8 default encoding ;-)
        pass

def main(argv):                                            # ||:fnc:||
    global _quiet, _debug, _verbose

    _parameters = None
    _pass_opts = []
    try:
        import argparse
    except ImportError:
        printe('error: argparse missing. Try `easy_install argparse`.')
        sys.exit(1)

    parser = argparse.ArgumentParser(add_help=False)
    # parser.add_argument('--sum', dest='accumulate', action='store_const',
    #                    const=sum, default=max,
    #                    help='sum the integers (default: find the max)')
    # |:opt:| add options
    parser.add_argument(
        '-q', '--quiet', action='store_true',
        help='suppress warnings')
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='verbose test output')
    parser.add_argument(
        '-d', '--debug', nargs='?', action='store', type=int, metavar='NUM',
        default = 0, const = 1,
        help='show debug information')
    parser.add_argument(
        '-t', '--test', action='store_true',
        help='run doc tests')
    parser.add_argument(
        '-h', '--help', action='store_true',
        help="display this help message")
    parser.add_argument(
        '--ap-help', action='store_true',
        help="internal help message")
    parser.add_argument(
        'args', nargs='*', metavar='arg',
        #'args', nargs='+', metavar='arg',
        #type=argparse.FileType('r'), default=sys.stdin,
        help='a series of arguments')

    #_parameters = parser.parse_args()
    (_parameters, _pass_opts) = parser.parse_known_args()
    # generate argparse help
    if _parameters.ap_help:
        parser.print_help()
        sys.exit(0)
    # standard help
    if _parameters.help:
        sys.stdout.write(__doc__)
        sys.exit(0)

    # at least use `quiet` to suppress the setdefaultencoding warning
    setdefaultencoding(quiet=_parameters.quiet or _parameters.test)

    _debug = _parameters.debug
    if _debug:
        _parameters.verbose = True
    _verbose = _parameters.verbose
    if _verbose:
        _parameters.quiet = False
    _quiet = _parameters.quiet
    # |:opt:| handle options

    # run doc tests
    if _parameters.test:
        import doctest
        doctest.testmod(verbose = _verbose)
        sys.exit()

    if _debug:
        cmd_line = sys.argv
        sys.stderr.write(sformat(
                "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[\n",
                globals()['dbg_comm'] if 'dbg_comm' in globals() else '# ',
                globals()['dbg_twid'] if 'dbg_twid' in globals() else 9,
                globals()['dbg_fwid'] if 'dbg_fwid' in globals() else 15,
                ':DBG:', 'cmd_line', cmd_line))

    run(_parameters, _pass_opts)

if __name__ == "__main__":
    #sys.argv.insert(1, '--debug') # |:debug:|
    main(sys.argv)
    sys.exit()

    # |:here:|

# (progn (forward-line 1) (snip-insert-mode "py.t.ide" t) (insert "\n"))
#
# :ide-menu: Emacs IDE Main Menu - Buffer @BUFFER@
# . M-x `eIDE-menu' (eIDE-menu "z")

# :ide: COMPILE: Run with python3 w/o args
# . (progn (save-buffer) (compile (concat "python3 ./" (file-name-nondirectory (buffer-file-name)) " ")))

# :ide: +-#+
# . Python 3 ()

# :ide: CSCOPE ON
# . (cscope-minor-mode)

# :ide: CSCOPE OFF
# . (cscope-minor-mode (quote ( nil )))

# :ide: TAGS: forced update
# . (compile (concat "cd /home/ws/project/ws-rfid && make -k FORCED=1 tags"))

# :ide: TAGS: update
# . (compile (concat "cd /home/ws/project/ws-rfid && make -k tags"))

# :ide: +-#+
# . Utilities ()

# :ide: TOC: Generate TOC with py-toc.py
# . (progn (save-buffer) (compile (concat "py-toc.py ./" (file-name-nondirectory (buffer-file-name)) " ")))

# :ide: CMD: Fold region with line continuation
# . (shell-command-on-region (region-beginning) (region-end) "fold --spaces -width 79 | sed 's, $,,;1!s,^, ,;$!s,$,\\\\,'" nil nil nil t)

# :ide: CMD: Fold region and replace with line continuation
# . (shell-command-on-region (region-beginning) (region-end) "fold --spaces --width 79 | sed 's, $,,;1!s,^, ,;$!s,$,\\\\,'" t nil nil t)

# :ide: +-#+
# . Fold ()

# :ide: CMD: Remove 8 spaces and add `>>> ' to region
# . (shell-command-on-region (region-beginning) (region-end) "sed 's,^        ,,;/^[ ]*##/d;/^[ ]*#/{;s,^ *# *,,p;d;};/^[ ]*$/!s,^,>>> ,'" nil nil nil t)

# :ide: CMD: Remove 4 spaces and add `>>> ' to region
# . (shell-command-on-region (region-beginning) (region-end) "sed 's,^    ,,;/^[ ]*##/d;/^[ ]*#/{;s,^ *# *,,p;d;};/^[ ]*$/!s,^,>>> ,'" nil nil nil t)

# :ide: +-#+
# . Doctest ()

# :ide: LINT: Check 80 column width ignoring IDE Menus
# . (let ((args " | /srv/ftp/pub/check-80-col.sh -")) (compile (concat "sed 's,^\\(\\|. \\|.. \\|... \\)\\(:ide\\|[.] \\).*,,' " (buffer-file-name) " " args " | sed 's,^-," (buffer-file-name) ",'")))

# :ide: LINT: Check 80 column width
# . (let ((args "")) (compile (concat "/srv/ftp/pub/check-80-col.sh " (buffer-file-name) " " args)))

# :ide: +-#+
# . Lint Tools ()

# :ide: DELIM:     @: SYM :@         @:fillme:@             adhoc tag
# . (symbol-tag-normalize-delimiter (cons (cons nil "@:") (cons ":@" nil)) t)

# :ide: +-#+
# . Delimiters ()

# :ide: COMPILE: Run with --ap-help
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " --ap-help")))

# :ide: COMPILE: Run with --help
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " --help")))

# :ide: COMPILE: Run with --test
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " --test")))

# :ide: COMPILE: Run with --test --verbose
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " --test --verbose")))

# :ide: COMPILE: Run with --debug
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " --debug")))

# :ide: +-#+
# . Compile with standard arguments ()

# :ide: OCCUR-OUTLINE: Python Source Code
# . (x-symbol-tag-occur-outline "sec" '("|||:" ":|||") (cons (cons "^\\([ \t\r]*\\(def\\|class\\)[ ]+\\|[A-Za-z_]?\\)" nil) (cons nil "\\([ \t\r]*(\\|[ \t]*=\\)")))

# :ide: MENU-OUTLINE: Python Source Code
# . (x-eIDE-menu-outline "sec" '("|||:" ":|||") (cons (cons "^\\([ \t\r]*\\(def\\|class\\)[ ]+\\|[A-Za-z_]?\\)" nil) (cons nil "\\([ \t\r]*(\\|[ \t]*=\\)")))

# :ide: +-#+
# . Outline ()

# :ide: INFO: SQLAlchemy - SQL Expression Language - Reference
# . (let ((ref-buffer "*sqa-expr-ref*")) (if (not (get-buffer ref-buffer)) (shell-command (concat "w3m -dump -cols " (number-to-string (1- (window-width))) " 'http://www.sqlalchemy.org/docs/05/reference/sqlalchemy/expressions.html'") ref-buffer) (display-buffer ref-buffer t)))

# :ide: INFO: SQLAlchemy - SQL Expression Language - Tutorial
# . (let ((ref-buffer "*sqa-expr-tutor*")) (if (not (get-buffer ref-buffer)) (shell-command (concat "w3m -dump -cols " (number-to-string (1- (window-width))) " 'http://www.sqlalchemy.org/docs/05/sqlexpression.html'") ref-buffer) (display-buffer ref-buffer t)))

# :ide: INFO: SQLAlchemy - Query
# . (let ((ref-buffer "*sqa-query*")) (if (not (get-buffer ref-buffer)) (shell-command (concat "w3m -dump -cols " (number-to-string (1- (window-width))) " 'http://www.sqlalchemy.org/docs/orm/query.html'") ref-buffer) (display-buffer ref-buffer t)))

# :ide: +-#+
# . SQLAlchemy Reference ()

# :ide: INFO: Python - argparse
# . (let ((ref-buffer "*python-argparse*")) (if (not (get-buffer ref-buffer)) (shell-command (concat "w3m -dump -cols " (number-to-string (1- (window-width))) " 'http://docs.python.org/library/argparse.html'") ref-buffer) (display-buffer ref-buffer t)))

# :ide: INFO: Python Documentation
# . (let ((ref-buffer "*w3m*")) (if (get-buffer ref-buffer) (display-buffer ref-buffer t)) (other-window 1) (w3m-goto-url "http://docs.python.org/index.html" nil nil))

# :ide: INFO: Python Reference
# . (let ((ref-buffer "*python-ref*")) (if (not (get-buffer ref-buffer)) (shell-command (concat "w3m -dump -cols " (number-to-string (1- (window-width))) " 'http://rgruet.free.fr/PQR27/PQR2.7.html'") ref-buffer) (display-buffer ref-buffer t)))

# :ide: +-#+
# . Python Reference ()

# :ide: COMPILE: Run with python3 with --test
# . (progn (save-buffer) (compile (concat "python3 ./" (file-name-nondirectory (buffer-file-name)) " --test")))

# :ide: COMPILE: Run with python3 w/o args
# . (progn (save-buffer) (compile (concat "python3 ./" (file-name-nondirectory (buffer-file-name)) " ")))

# :ide: COMPILE: Run with --test
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " --test")))

# :ide: COMPILE: Run w/o args
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " ")))

# :ide: +-#+
# . Compile ()

#
# Local Variables:
# mode: python
# comment-start: "#"
# comment-start-skip: "#+"
# comment-column: 0
# truncate-lines: t
# End:
