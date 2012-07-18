#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------------------------------------
# |||:sec:||| COMPATIBILITY
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

import os
import re

try:
    reduce
except NameError:
    from functools import reduce

# --------------------------------------------------
# |||:sec:||| FUNCTIONS
# --------------------------------------------------

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

def printe(*args, **kwargs):                               # ||:fnc:||
    kwargs['file'] = kwargs.get('file', sys.stderr)
    printf(*args, **kwargs)

# --------------------------------------------------
# |||:sec:||| APPLICATION
# --------------------------------------------------

import traceback
import random
import time
from datetime import datetime
import json

import bson
if hasattr(bson, 'enable_getstate'):
    bson_enable_c = bson
    def is_c_enabled():
        return bson._ctx._use_c_encoding or bson._ctx._use_c_decoding
    bson.is_c_enabled = is_c_enabled
else:
    import bson_enable_c
import bson.json_util

DATA_COUNT = 1000
CYCLES = 100
CONVERTIBLE_COUNT = 1
MAX_CONVERTIBLE_COUNT = 5

def make_data():
    data = bson.SON([('key' + str(i), i) for i in range(DATA_COUNT)])
    return data

def make_key(data):
    key_indx = random.randint(0, len(data) - MAX_CONVERTIBLE_COUNT)
    return ('key' + str(key_indx), key_indx)

DATA = make_data()
KEYS = [make_key(DATA) for indx in range(CYCLES)]

class FlatConvertible(object):

    def __getstate__(self):
        return dict(vars(self))

    def __bson__(self):
        return { '_$class': self.__class__.__name__, '$_state': self.__getstate__() }

class DeepConvertible(FlatConvertible):

    def __getstate__(self):
        d = dict(vars(self))
        d.update({'a': FlatConvertible(), 'b': FlatConvertible()})
        return d

class KaputtConvertible(FlatConvertible):

    def __getstate__(self):
        raise TypeError("not with me, you don't!")

CONVERTIBLE = FlatConvertible

class waste_of_time_Encoder(json.JSONEncoder):
    def default(self, obj):
        try:
            serialized = bson.json_util.default(obj)
            failed = False
        except TypeError:
            failed = true
            self.wt = self.totally_wasted_time

        if not failed:
            return serialized
        return json.JSONEncoder.default(self, obj)

def report_times(total_time, wasted_time=None, totally_wasted_time=None, ref_time=None, json_time=None, bson_time=None):
    now = datetime.now()
    tzero = now - now
    hl_ok = False
    if json_time is not None:
        hl_ok = True
        json_time.append(tzero)
        json_time_sum = reduce(lambda x, y: x + y, json_time)
        json_time_avg = json_time_sum / CYCLES
        print('json_time_sum (' + str(CYCLES) + '/' + str(DATA_COUNT) + ')        : ' + str(json_time_sum))
        print('json_time_avg (' + str(CYCLES) + '/' + str(DATA_COUNT) + ')        : ' + str(json_time_avg))

    if bson_time is not None:
        hl_ok = True
        bson_time.append(tzero)
        bson_time_sum = reduce(lambda x, y: x + y, bson_time)
        bson_time_avg = bson_time_sum / CYCLES
        print('bson_time_sum (' + str(CYCLES) + '/' + str(DATA_COUNT) + ')        : ' + str(bson_time_sum))
        print('bson_time_avg (' + str(CYCLES) + '/' + str(DATA_COUNT) + ')        : ' + str(bson_time_avg))

    if wasted_time is not None:
        hl_ok = True
        wasted_time.append(tzero)
        wasted_time_sum = reduce(lambda x, y: x + y, wasted_time)
        wasted_time_avg = wasted_time_sum / CYCLES
        print('wasted_time_sum (' + str(CYCLES) + '/' + str(DATA_COUNT) + ')        : ' + str(wasted_time_sum))
        print('wasted_time_avg (' + str(CYCLES) + '/' + str(DATA_COUNT) + ')        : ' + str(wasted_time_avg))

    if totally_wasted_time is not None:
        hl_ok = True
        totally_wasted_time.append(tzero)
        totally_wasted_time_sum = reduce(lambda x, y: x + y, totally_wasted_time)
        totally_wasted_time_avg = totally_wasted_time_sum / CYCLES
        print('totally_wasted_time_sum (' + str(CYCLES) + '/' + str(DATA_COUNT) + '): ' + str(totally_wasted_time_sum))
        print('totally_wasted_time_avg (' + str(CYCLES) + '/' + str(DATA_COUNT) + '): ' + str(totally_wasted_time_avg))

        if wasted_time is not None:
            overall_wasted_time_sum = wasted_time_sum + totally_wasted_time_sum
            overall_wasted_time_avg = wasted_time_avg + totally_wasted_time_avg
            print('overall_wasted_time_sum (' + str(CYCLES) + '/' + str(DATA_COUNT) + '): ' + str(overall_wasted_time_sum))
            print('overall_wasted_time_avg (' + str(CYCLES) + '/' + str(DATA_COUNT) + '): ' + str(overall_wasted_time_avg))

    if total_time is not None:
        if hl_ok:
            hl()
        if ref_time is not None:
            factor = ' factor: ' + str(
                round((float(total_time.seconds * 1000000 + total_time.microseconds)
                       / (ref_time.seconds * 1000000 + ref_time.microseconds)) * 100)
                / 100)
        else:
            factor = ''
        print('total_time (' + str(CYCLES) + '/' + str(DATA_COUNT) + ')             : ' + str(total_time) + factor)

def waste_some_time_running_into_an_exception():
    data = DATA
    wasted_time = []
    total_start = datetime.now()
    first = True
    for indx in range(CYCLES):
        key, key_indx = KEYS[indx]
        data[key] = list
        start = datetime.now()
        try:
            bson.BSON.encode(data)
        except Exception:
            if first:
                (t, e, tb) = sys.exc_info()
                print("{0}{3:^{1}} {4:<{2}s}: ]{5!s}[".format(
                    '#', 9, 15, ':DBG:', 'e', type(e)))
                if hasattr(e, 'bson_error_parent'):
                    parent = e.bson_error_parent
                    if parent is not None:
                        lp = len(parent)
                    else:
                        lp = -1
                    print("{0}{3:^{1}} {4:<{2}s}: ]{5!s}[".format(
                        '#', 9, 15, ':DBG:', 'e.bson_error_parent', lp))
                if hasattr(e, 'bson_error_key') and e.bson_error_key is not None:
                    print("{0}{3:^{1}} {4:<{2}s}: ]{5!s}[".format(
                        '#', 9, 15, ':DBG:', 'e.bson_error_key', e.bson_error_key))
                if hasattr(e, 'bson_error_value'):
                    print("{0}{3:^{1}} {4:<{2}s}: ]{5!s}[".format(
                        '#', 9, 15, ':DBG:', 'e.bson_error_value', e.bson_error_value))
                #printe(''.join(traceback.format_tb(tb)))
                printf(sformat('{0}: {1}', t.__name__, e))
                first = False
        end = datetime.now()
        wasted_time.append(end-start)
        data[key] = key_indx
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, wasted_time, ref_time=total_time)
    total_time = total_end-total_start
    return total_time

def check_type_with_json_then_bson(key, val, dcopy, wt, totally_wasted_time, json_time, bson_time):
    start = datetime.now()
    try:
        # if it is JSON encodable, it is also BSON encodable
        json.dumps(val)
        dcopy[key] = val
        end = datetime.now()
        wt.append(end-start)
        #json_time.append(end-start)
    except TypeError:
        try:
            # BSON encodable
            bson.json_util.default(val)
            dcopy[key] = val
            end = datetime.now()
            wt.append(end-start)
            #bson_time.append(end-start)
        except TypeError:
            state = val.__getstate__()
            dcopy[key] = state
            end = datetime.now()
            wt.append(end-start)
            for key, val in state.items():
                check_type_with_json_then_bson(key, val, state, wt, totally_wasted_time, json_time, bson_time)
            wt = totally_wasted_time
    return wt

def waste_some_space_and_time_converting_data_with_json_bson_default(ref_time):
    # works always
    data = DATA
    dcopy = dict()
    json_time = []
    bson_time = []
    wasted_time = []
    totally_wasted_time = []
    total_start = datetime.now()
    for indx in range(CYCLES):
        dcopy = dict()
        key, key_indx = KEYS[indx]
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = CONVERTIBLE()
        wt = wasted_time
        for key, val in data.items():
            wt = check_type_with_json_then_bson(key, val, dcopy, wt, totally_wasted_time, json_time, bson_time)
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = key_indx + indx2
        bson.BSON.encode(dcopy)
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, wasted_time, totally_wasted_time, ref_time=ref_time, json_time=json_time, bson_time=bson_time)
    return total_time

def check_type_with_BSON_encode(key, val, dcopy, wt, totally_wasted_time):
    start = datetime.now()
    try:
        # BSON encodable
        bson.BSON.encode({ 'd': val }, check_keys=False)
        dcopy[key] = val
        end = datetime.now()
        wt.append(end-start)
    except bson.errors.InvalidDocument:
        state = val.__getstate__()
        dcopy[key] = state
        end = datetime.now()
        wt.append(end-start)
        for key, val in state.items():
            check_type_with_BSON_encode(key, val, state, wt, totally_wasted_time)
        wt = totally_wasted_time
    return wt

def waste_some_space_and_time_converting_data_with_BSON_encode(ref_time):
    # works always
    data = DATA
    dcopy = dict()
    wasted_time = []
    totally_wasted_time = []
    total_start = datetime.now()
    for indx in range(CYCLES):
        dcopy = dict()
        key, key_indx = KEYS[indx]
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = CONVERTIBLE()
        wt = wasted_time
        for key, val in data.items():
            wt = check_type_with_BSON_encode(key, val, dcopy, wt, totally_wasted_time)
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = key_indx + indx2
        bson.BSON.encode(dcopy)
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, wasted_time, totally_wasted_time, ref_time=ref_time)
    return total_time

def check_type_with_dict_to_bson_buggy(key, val, dcopy, wt, totally_wasted_time):
    start = datetime.now()
    try:
        # BSON encodable
        bson._dict_to_bson({ 'd': val }, False, bson.OLD_UUID_SUBTYPE)
        dcopy[key] = val
        end = datetime.now()
        wt.append(end-start)
    except bson.errors.InvalidDocument:
        state = val.__getstate__()
        dcopy[key] = state
        end = datetime.now()
        wt.append(end-start)
        for key, val in state.items():
            check_type_with_dict_to_bson_buggy(key, val, state, wt, totally_wasted_time)
        wt = totally_wasted_time
    return wt

def waste_some_space_and_time_converting_data_with_dict_to_bson_buggy(ref_time):
    # works always
    data = DATA
    dcopy = dict()
    wasted_time = []
    totally_wasted_time = []
    total_start = datetime.now()
    for indx in range(CYCLES):
        dcopy = dict()
        key, key_indx = KEYS[indx]
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = CONVERTIBLE()
        wt = wasted_time
        for key, val in data.items():
            wt = check_type_with_dict_to_bson_buggy(key, val, dcopy, wt, totally_wasted_time)
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = key_indx + indx2
        bson.BSON.encode(dcopy)
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, wasted_time, totally_wasted_time, ref_time=ref_time)
    return total_time

def check_type_with_dict_to_bson_fixed(key, val, dcopy, wt, totally_wasted_time):
    start = datetime.now()
    try:
        # BSON encodable
        bson._dict_to_bson({ 'd': val }, False, bson.OLD_UUID_SUBTYPE, False)
        dcopy[key] = val
        end = datetime.now()
        wt.append(end-start)
    except bson.errors.InvalidDocument:
        state = val.__getstate__()
        dcopy[key] = state
        end = datetime.now()
        wt.append(end-start)
        for key, val in state.items():
            check_type_with_dict_to_bson_fixed(key, val, state, wt, totally_wasted_time)
        wt = totally_wasted_time
    return wt

def waste_some_space_and_time_converting_data_with_dict_to_bson_fixed(ref_time):
    # works always
    data = DATA
    dcopy = dict()
    wasted_time = []
    totally_wasted_time = []
    total_start = datetime.now()
    for indx in range(CYCLES):
        dcopy = dict()
        key, key_indx = KEYS[indx]
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = CONVERTIBLE()
        wt = wasted_time
        for key, val in data.items():
            wt = check_type_with_dict_to_bson_fixed(key, val, dcopy, wt, totally_wasted_time)
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = key_indx + indx2
        bson.BSON.encode(dcopy)
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, wasted_time, totally_wasted_time, ref_time=ref_time)
    return total_time

def check_type_with_element_to_bson(key, val, dcopy, wt, totally_wasted_time):
    start = datetime.now()
    try:
        # BSON encodable, private API
        bson._element_to_bson('d', val, False, bson.OLD_UUID_SUBTYPE)
        dcopy[key] = val
        end = datetime.now()
        wt.append(end-start)
    except bson.errors.InvalidDocument:
        state = val.__getstate__()
        dcopy[key] = state
        end = datetime.now()
        wt.append(end-start)
        for key, val in state.items():
            check_type_with_element_to_bson(key, val, state, wt, totally_wasted_time)
        wt = totally_wasted_time
    return wt

def waste_some_space_and_time_converting_data_with_element_to_bson(ref_time):
    # works always
    data = DATA
    dcopy = dict()
    wasted_time = []
    totally_wasted_time = []
    total_start = datetime.now()
    for indx in range(CYCLES):
        dcopy = dict()
        key, key_indx = KEYS[indx]
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = CONVERTIBLE()
        wt = wasted_time
        for key, val in data.items():
            wt = check_type_with_element_to_bson(key, val, dcopy, wt, totally_wasted_time)
        for indx2 in range(CONVERTIBLE_COUNT):
            data['key' + str(key_indx+indx2)] = key_indx + indx2
        bson.BSON.encode(dcopy)
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, wasted_time, totally_wasted_time, ref_time=ref_time)
    return total_time

def waste_some_time_with_wrapped_python_element_to_bson(ref_time):
    # works always
    data = DATA
    total_start = datetime.now()
    wasted_time = []

    sv_c_active = bson.is_c_enabled()
    sv_element_to_bson = bson._element_to_bson
    bson.enable_c_encoding(False)
    def _element_to_bson(key, value, *args):
        try:
            return sv_element_to_bson(key, value, *args)
        except bson.errors.InvalidDocument:
            pass
        start = datetime.now()
        state = value.__getstate__()
        end = datetime.now()
        wasted_time.append(end-start)
        return sv_element_to_bson(key, state, *args)
    bson._element_to_bson = _element_to_bson

    try:
        for indx in range(CYCLES):
            dcopy = dict()
            key, key_indx = KEYS[indx]
            for indx2 in range(CONVERTIBLE_COUNT):
                data['key' + str(key_indx+indx2)] = CONVERTIBLE()
            # encode with wrapped _element_to_bson
            bson.BSON.encode(data)
            for indx2 in range(CONVERTIBLE_COUNT):
                data['key' + str(key_indx+indx2)] = key_indx + indx2
    except Exception:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    bson._element_to_bson = sv_element_to_bson
    bson.enable_c(sv_c_active)
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, wasted_time, ref_time=ref_time)
    return total_time

def dont_waste_time_with_getstate_hook_feature(ref_time):
    # works always

    try:
        sv_getstate_hook_enabled = bson.is_getstate_hook_enabled()
    except AttributeError:
        try:
            sv_getstate_hook_enabled = bson.is_getstate_enabled()
        except AttributeError:
            printe('SKIPPED')
            return

    try:
        bson.enable_getstate_hook(True)
    except AttributeError:
        try:
            bson.enable_getstate(True)
        except AttributeError:
            printe('SKIPPED')
            return

    data = DATA
    total_start = datetime.now()

    try:
        for indx in range(CYCLES):
            dcopy = dict()
            key, key_indx = KEYS[indx]
            for indx2 in range(CONVERTIBLE_COUNT):
                data['key' + str(key_indx+indx2)] = CONVERTIBLE()
            # encode with getstate_hook
            bson.BSON.encode(data)
            for indx2 in range(CONVERTIBLE_COUNT):
                data['key' + str(key_indx+indx2)] = key_indx + indx2
    except Exception:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    try:
        bson.enable_getstate_hook(sv_getstate_hook_enabled)
    except AttributeError:
        bson.enable_getstate(sv_getstate_hook_enabled)
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, ref_time=ref_time)
    return total_time

def dont_waste_time_with_dict_hook_feature(ref_time):
    # works always

    try:
        sv_dict_hook_enabled = bson.is_dict_hook_enabled()
    except AttributeError:
        printe('SKIPPED')
        return

    try:
        bson.enable_dict_hook(True)
    except AttributeError:
        printe('SKIPPED')
        return

    data = DATA
    total_start = datetime.now()

    try:
        for indx in range(CYCLES):
            dcopy = dict()
            key, key_indx = KEYS[indx]
            for indx2 in range(CONVERTIBLE_COUNT):
                data['key' + str(key_indx+indx2)] = CONVERTIBLE()
            # encode with dict_hook
            bson.BSON.encode(data)
            for indx2 in range(CONVERTIBLE_COUNT):
                data['key' + str(key_indx+indx2)] = key_indx + indx2
    except Exception:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    bson.enable_dict_hook(sv_dict_hook_enabled)
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, ref_time=ref_time)
    return total_time

def dont_waste_time_with_bson_hook_feature(ref_time):
    # works always

    try:
        sv_bson_hook_enabled = bson.is_bson_hook_enabled()
    except AttributeError:
        printe('SKIPPED')
        return

    try:
        bson.enable_bson_hook(True)
    except AttributeError:
        printe('SKIPPED')
        return

    data = DATA
    total_start = datetime.now()

    try:
        for indx in range(CYCLES):
            dcopy = dict()
            key, key_indx = KEYS[indx]
            for indx2 in range(CONVERTIBLE_COUNT):
                data['key' + str(key_indx+indx2)] = CONVERTIBLE()
            # encode with bson_hook
            bson.BSON.encode(data)
            for indx2 in range(CONVERTIBLE_COUNT):
                data['key' + str(key_indx+indx2)] = key_indx + indx2
    except Exception:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    bson.enable_bson_hook(sv_bson_hook_enabled)
    total_end = datetime.now()
    total_time = total_end-total_start
    report_times(total_time, ref_time=ref_time)
    return total_time

def test_run():                                            # ||:fnc:||

    try:
        hl('waste_some_time_running_into_an_exception() (reference time)')
        bson.enable_c(True)
        ref_time = waste_some_time_running_into_an_exception()
    except:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))
        ref_time = None

    try:
        hl('waste_some_space_and_time_converting_data_with_json_bson_default()')
        bson.enable_c(True)
        waste_some_space_and_time_converting_data_with_json_bson_default(ref_time)
    except:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    try:
        hl('waste_some_space_and_time_converting_data_with_BSON_encode()')
        bson.enable_c(True)
        waste_some_space_and_time_converting_data_with_BSON_encode(ref_time)
    except:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    try:
        hl('waste_some_space_and_time_converting_data_with_dict_to_bson_buggy()')
        bson.enable_c(True)
        waste_some_space_and_time_converting_data_with_dict_to_bson_buggy(ref_time)
    except:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    hl('waste_some_space_and_time_converting_data_with_dict_to_bson_fixed()')
    try:
        bson._dict_to_bson({ 'd': 1 }, False, bson.OLD_UUID_SUBTYPE, False)
        try:
            bson.enable_c(True)
            waste_some_space_and_time_converting_data_with_dict_to_bson_fixed(ref_time)
        except:
            (t, e, tb) = sys.exc_info()
            printe(''.join(traceback.format_tb(tb)))
            printf(sformat('{0}: {1}', t.__name__, e))
    except TypeError:
        printe('SKIPPED')

    try:
        hl('waste_some_space_and_time_converting_data_with_element_to_bson()')
        bson.enable_c(True)
        waste_some_space_and_time_converting_data_with_element_to_bson(ref_time)
    except:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    try:
        hl('waste_some_time_with_wrapped_python_element_to_bson()')
        bson.enable_c(True)
        waste_some_time_with_wrapped_python_element_to_bson(ref_time)
    except:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    try:
        hl('dont_waste_time_with_getstate_hook_feature()')
        bson.enable_c(True)
        dont_waste_time_with_getstate_hook_feature(ref_time)
    except:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    try:
        hl('dont_waste_time_with_dict_hook_feature()')
        bson.enable_c(True)
        dont_waste_time_with_dict_hook_feature(ref_time)
    except:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

    try:
        hl('dont_waste_time_with_bson_hook_feature()')
        bson.enable_c(True)
        dont_waste_time_with_bson_hook_feature(ref_time)
    except:
        (t, e, tb) = sys.exc_info()
        printe(''.join(traceback.format_tb(tb)))
        printf(sformat('{0}: {1}', t.__name__, e))

def run(parameters, pass_opts):                            # ||:fnc:||
    """Application runner, when called as __main__."""

    dbg_comm = globals()['dbg_comm'] if 'dbg_comm' in globals() else '# '
    dbg_twid = globals()['dbg_twid'] if 'dbg_twid' in globals() else 9
    dbg_fwid = globals()['dbg_fwid'] if 'dbg_fwid' in globals() else 16

    # (progn (forward-line 1) (snip-insert-mode "py.bf.sql.ws" t) (insert "\n"))
    # (progn (forward-line 1) (snip-insert-mode "py.bf.file.arg.loop" t) (insert "\n"))

    #bson.enable_c(False)
    #waste_some_time_running_into_an_exception()

    global CONVERTIBLE, CONVERTIBLE_COUNT

    hl_lvl(1)
    hl('CONVERTIBLE=FlatConvertible (1)')
    hl_lvl(0)
    CONVERTIBLE=FlatConvertible
    CONVERTIBLE_COUNT = 1
    hl('waste_some_time_running_into_an_exception()')
    bson.enable_c(True)
    waste_some_time_running_into_an_exception()
    test_run()

    hl_lvl(1)
    hl('CONVERTIBLE=DeepConvertible (1)')
    hl_lvl(0)
    CONVERTIBLE=DeepConvertible
    CONVERTIBLE_COUNT = 1
    test_run()

    hl_lvl(1)
    hl('CONVERTIBLE=DeepConvertible (5)')
    hl_lvl(0)
    CONVERTIBLE=DeepConvertible
    CONVERTIBLE_COUNT = 5
    test_run()

    hl_lvl(1)
    hl('CONVERTIBLE=KaputtConvertible (1)')
    hl_lvl(0)
    CONVERTIBLE=KaputtConvertible
    CONVERTIBLE_COUNT = 1
    test_run()

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

# :ide: COMPILE: Run with python3 w/o args
# . (progn (save-buffer) (compile (concat "python3 ./" (file-name-nondirectory (buffer-file-name)) " ")))

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
