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
check_000_getstate.py - ::fillme::

======  ====================
usage:  check_000_getstate.py [OPTIONS] ::fillme::
or      import check_000_getstate
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

# (progn (forward-line 1) (snip-insert-mode "py.f.issequence" t) (insert "\n"))
def issequence(arg, or_dict=False):                        # ||:fnc:||
    """Does not consider strings a sequence.

    >>> def check_issequence():
    ...     for check_seq in ('hello', dict(), list(), reversed(list()), tuple(), dict().items()): #doctest: +ELLIPSIS
    ...         isseq = issequence(check_seq)
    ...         check_seqr = re.sub(' at 0x[0-9a-f]+', '', repr(check_seq))
    ...         print(sformat(
    ...                 "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
    ...                 '#', 9, 29, ':DBG:', check_seqr, isseq))
    >>> check_issequence()  #doctest: +ELLIPSIS
    #  :DBG:   'hello'                      : ]False[
    #  :DBG:   {}                           : ]False[
    #  :DBG:   []                           : ]True[
    #  :DBG:   <...reverseiterator object...: ]True[
    #  :DBG:   ()                           : ]True[
    #  :DBG:   ...[]... ... ...             : ]True[
    """
    if not isstring(arg):
        if hasattr(arg, 'items'):
            return or_dict
        try:
            for elt in arg:
                break
            return True
        except TypeError:
            pass
    return False

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

import os
import re

dbg_comm = globals()['dbg_comm'] if 'dbg_comm' in globals() else '# '
dbg_twid = globals()['dbg_twid'] if 'dbg_twid' in globals() else 9
dbg_fwid = globals()['dbg_fwid'] if 'dbg_fwid' in globals() else 17

import warnings
import pickle
import json
import bson
import bson.json_util
from bson import BSON

# --------------------------------------------------
# |||:sec:||| Feature test
# --------------------------------------------------

try:
    import pyjsmox
except ImportError:
    import copy
    try:
        import bson.son
        _pyjsmo_od = bson.son.SON
    except (ImportError, AttributeError):
        try:
            _pyjsmo_od = OrderedDict
            printf('Using OrderedDict')
        except NameError:
            _pyjsmo_od = dict
            printf('Using dict')
    class pyjsmo(object):
        OrderedDict = _pyjsmo_od
        class PyJsMo(object):
            _pyjsmo_order = []
            _pyjsmo_defaults = OrderedDict()
            def __init__(self):
                self._pyjsmo_order = list(self._pyjsmo_order)
                for attr in self._pyjsmo_order:
                    setattr(self, attr, None)
                for key, val in self._pyjsmo_defaults.items():
                    if key not in self._pyjsmo_order:
                        self._pyjsmo_order.append(key)
                    setattr(self, key, copy.deepcopy(val))
            def asDict(self):
                state = OrderedDict()
                for attr in self._pyjsmo_order:
                    value = getattr(self, attr)
                    state[attr] = value
                return state
            def __iter__(self):
                return self.keys().__iter__()
            def __getitem__(self, key):
                try:
                    return getattr(self, key)
                except AttributeError:
                    raise KeyError(key)
            def __setitem__(self, key, value):
                return setattr(self, key, value)
            def keys(self):
                 return self.asDict().keys()
            def values(self):
                 return self.asDict().values()
            def items(self):
                 return self.asDict().items()
    del(_pyjsmo_od)

import threading

class BSONConfig(pyjsmo.PyJsMo):                                  # ||:cls:||
    """BSON Feature Configuration.

    All features in BSON are enabled/disabled through feature
    functions.

    The feature functions are indirectly accessed through
    `set_<feature>` methods, which ultimmate call :meth:`_setFeature`,
    which in turn does nothing, if a feature is not available.

    The set_<feature> methods can also be accessed without the `set_`
    prefix. They are internally redirected to overloaded
    `set_<feature>` methods or :meth:`_setFeature` as appropriate.

    The feature status is uniformly accessed through `is_`
    methods, which can optionally be overloaded.

    Feature data is accessed through `get_` methods and the values are
    modified through `set_` methods. Feature data can also be
    retrieved without the `get_` prefix.

    :meth:`lock` and :meth:`unlock` are used to serialize access to
    the global configuration::

      force = False # only lock BSON, if threading is not enabled
      force = True  # always lock BSON (default)

      context = bc.lock(force)
      # configure BSON
      bc.enable_c()
      bc.enable_dict()
      if context is not None:
          my_context = bc.get_context()
      else:
          my_context = None
      bc.unlock(context)

      while not done:
          context = bc.lock(force)
          bc.set_context(my_context)

          # do BSON stuff ...

          bc.unlock(context)

     If threading support is enabled and argument `force` is False,
     the :meth:`lock` method does nothing and returns a `None`
     context. The :meth:`unlock` method does nothing, if a `None`
     context is supplied.

    >>> bc = BSONConfig()

    >>> ((bc.have_enable_c and bc.enable_c(True) == True) or
    ...  (not bc.have_enable_c and bc.enable_c(True) is None))
    True

    >>> bc.is_dict_enabled() == False
    True

    >>> bc.enable_dict()
    >>> ((bc.have_enable_dict and bc.is_dict_enabled() == True) or
    ...  (not bc.have_enable_dict and bc.is_dict_enabled() == False))
    True

    >>> bc.is_something_enabled() == False
    True

    >>> bc.enable_threading()
    >>> ((bc.have_enable_threading and bc.is_threading_enabled() == True) or
    ...  (not bc.have_enable_threading and bc.is_threading_enabled() == False))
    True

    >>> ((bc.have_wrap_class_key and str(bc.wrap_class_key()) == '_$class') or
    ...  (not bc.have_wrap_class_key and bc.wrap_class_key() is None))
    True

    >>> bc.set_wrap_class_key('_$$_')
    >>> ((bc.have_wrap_class_key and str(bc.wrap_class_key()) == '_$$_') or
    ...  (not bc.have_wrap_class_key and bc.wrap_class_key() is None))
    True

    >>> printe(bc.status(short=True))
    >>> printe(bc.status())
    """

    #_pyjsmo_order = []
    _pyjsmo_defaults = pyjsmo.OrderedDict((
        # feature_attribute_in_bson,  [haveit, get_status]
        ('feature_has_c',             [False, 'has_c']),
        ('feature_enable_threading',  [False, 'is_threading_enabled']),
        ('feature_enable_c',          [False, 'is_c_enabled']),
        ('feature_enable_getstate',   [False, 'is_getstate_enabled']),
        ('feature_enable_dict',       [False, 'is_dict_enabled']),
        ('feature_enable_annotate',   [False, 'is_annotate_enabled']),
        ('feature_annotate_key',      [False, 'get_annotate_key']),
        ('feature_enable_wrap',       [False, 'is_wrap_enabled']),
        ('feature_wrap_class_key',    [False, 'get_wrap_class_key']),
        ('feature_wrap_state_key',    [False, 'get_wrap_state_key']),
        ('feature_default',           [False, 'have_default']),
        ('feature_get_element_state', [False, None]),
        ))
    #_pyjsmo_amap = []
    #_pyjsmo_safe = True
    _pyjsmo_x_lock = threading.Lock()

    @property
    def global_lock(self):                                   # |:mth:|
        return self._pyjsmo_x_lock

    def __init__(self):                                      # |:mth:|
        super(BSONConfig, self).__init__()
        if hasattr(bson, 'lock'):
            self._pyjsmo_x_lock = bson.lock
        self.checkFeatures()

    # --------------------------------------------------
    # ||:sec:|| Utilities
    # --------------------------------------------------

    def _bsonFeatureName(self, feature):                      # |:mth:|
        if feature.startswith('feature_'):
            return feature[len('feature_'):]
        return feature

    def featureState(self, feature, *args, **kwargs):         # |:mth:|
        '''Get configuration state variable for feature.'''
        if feature.startswith('feature_'):
            return getattr(self, feature)
        return getattr(self, ''.join(('feature_', feature)))

    def notAvail(self, *args, **kwargs):                     # |:mth:|
        return False

    # --------------------------------------------------
    # ||:sec:|| Locking
    # --------------------------------------------------

    def get_context(self):                                   # |:mth:|
        try:
            return bson._ctx.__getstate__()
        except AttributeError:
            return None

    def set_context(self, context):                          # |:mth:|
        if context is not None:
            try:
                bson._ctx.__setstate__(context)
            except AttributeError:
                pass

    def lock(self, force=True):                              # |:mth:|
        '''Lock access to the global context.

        If parameter `force` is False and threading is enabled the
        lock is not acquired and a `None` context is returned.

        :returns: global context state.
        '''
        if force or not self.is_threading_enabled():
            self.global_lock.acquire()
            return self.get_context()
        return None

    def unlock(self, context):                               # |:mth:|
        '''Unlock access to the global context, if threading is not
        enabled.

        :param context: global context state as returned by
          :meth:`lock`.
        '''
        if context is not None:
            self.set_context(context)
            self.global_lock.release()

    # --------------------------------------------------
    # ||:sec:|| Generic Attribute Handler
    # --------------------------------------------------

    class GetFeature(object):                              # ||:cls:||

        def __call__(self, *args, **kwargs):                 # |:mth:|
            return self.bc._getFeature(self.bfeature, *args, **kwargs)

        def __init__(self, bc, bfeature):                     # |:mth:|
            self.bc = bc
            self.bfeature = bfeature

    class SetFeature(object):                              # ||:cls:||

        def __call__(self, *args, **kwargs):                 # |:mth:|
            return self.bc._setFeature(self.bfeature, *args, **kwargs)

        def __init__(self, bc, bfeature):                     # |:mth:|
            self.bc = bc
            self.bfeature = bfeature

    def __getattr__(self, attr):                             # |:mth:|
        if attr.startswith('have_'):
            bfeature = attr[len('have_'):]
            try:
                return self.featureState(bfeature)[0]
            except AttributeError:
                return False
        if attr.startswith('is_'):
            try:
                return getattr(bson, attr)
            except AttributeError:
                return self.notAvail
        if attr.startswith('get_'):
            bfeature = attr[len('get_'):]
            if getattr(self, ''.join(('feature_', bfeature))):
                if self.featureState(bfeature)[1].startswith('get_'):
                    return BSONConfig.GetFeature(self, bfeature)
        if attr.startswith('set_'):
            bfeature = attr[len('set_'):]
            if getattr(self, ''.join(('feature_', bfeature))):
                return BSONConfig.SetFeature(self, bfeature)
        elif not attr.startswith('feature_'):
            if hasattr(self, ''.join(('feature_', attr))):
                try:
                    return getattr(self, ''.join(('get_', attr)))
                except AttributeError:
                    return getattr(self, ''.join(('set_', attr)))
        return super(BSONConfig, self).__getattribute__(attr)

    # --------------------------------------------------
    # ||:sec:|| Feature Check
    # --------------------------------------------------

    def checkFeature(self, feature):                         # |:mth:|
        bfeature = self._bsonFeatureName(feature)
        try:
            have_it = getattr(self, ''.join(('check_', bfeature)))()
        except AttributeError:
            try:
                getattr(bson, bfeature)
                have_it = True
            except AttributeError:
                have_it = False
        self.featureState(feature)[0] = have_it
        return have_it

    def checkFeatures(self):                                 # |:mth:|
        '''Check availability for all features.

        Can be called at any time to refresh the configuration state.'''
        for feature in self:
            self.checkFeature(feature)

    def check_get_element_state(self):                       # |:mth:|
        try:
            bson._element_to_bson(
                'key', 'value',
                False, bson.OLD_UUID_SUBTYPE,
                get_element_state=None)
            return True
        except TypeError:
            return False

    # --------------------------------------------------
    # ||:sec:|| Get Feature Data
    # --------------------------------------------------

    def _getFeature(self, bfeature, *args, **kwargs):         # |:mth:|
        if getattr(self, ''.join(('feature_', bfeature))):
            if self.featureState(bfeature)[0]:
                return getattr(bson, bfeature)(*args, **kwargs)

    def getFeature(self, feature, *args, **kwargs):          # |:mth:|
        bfeature = self._bsonFeatureName(feature)
        self._getFeature(bfeature, *args, **kwargs)

    # --------------------------------------------------
    # ||:sec:|| Enable/Disable Feature / Set Feature Data
    # --------------------------------------------------

    def _setFeature(self, bfeature, *args, **kwargs):         # |:mth:|
        if getattr(self, ''.join(('feature_', bfeature))):
            if self.featureState(bfeature)[0]:
                try:
                    return getattr(bson, ''.join(('set_', bfeature)))(*args, **kwargs)
                except AttributeError:
                    return getattr(bson, bfeature)(*args, **kwargs)

    def setFeature(self, feature, *args, **kwargs):          # |:mth:|
        bfeature = self._bsonFeatureName(feature)
        self._setFeature(bfeature, *args, **kwargs)

    # --------------------------------------------------
    # ||:sec:|| Status
    # --------------------------------------------------

    def is_c_enabled(self):                                  # |:mth:|
        if self.have_enable_c:
            return (bson._ctx._use_c_encoding
                    and bson._ctx._use_c_decoding)
        return bson.has_c()

    def status_name(self, status):                           # |:mth:|
        if status == True or status == False:
            return 'active'
        if status is None:
            return 'NA'
        return 'value'

    def status(self, fset=None, short=False, *args, **kwargs): # |:mth:|
        if fset is None:
            fset = self._pyjsmo_order
        output = []
        if short:
            sep = ', '
        else:
            sep = '\n'
        fwid = dbg_fwid if dbg_fwid > 17 else 17
        for feature in fset:
            param = self.featureState(feature)
            bfeature = self._bsonFeatureName(feature)
            have_it = param[0]
            status = param[1]
            if status is not None:
                status = getattr(self, status)
                if callable(status):
                    status = status()
            if short:
                if have_it and status is not None:
                    output.append(sformat('{0}: ]{1}[', bfeature, status))
            else:
                output.append(sformat(
                    "{0}{3:^{1}} {4:<{2}s}: {5!s:<3s} available, {6!s:<6}: ]{7!s:<7s}[",
                    dbg_comm, dbg_twid, fwid, ':FTR:', bfeature,
                    '' if have_it else 'not',
                    self.status_name(status), status))
        return sep.join(output)

# (progn (forward-line -1) (insert "\n") (snip-insert-mode "py.s.meth" t) (backward-symbol-tag 2 "fillme" "::"))

bc = BSONConfig()

have_get_element_state = bc.have_get_element_state
have_enable_c = bc.have_enable_c
have_enable_getstate = bc.have_enable_getstate

# (progn (forward-line 1) (snip-insert-mode "py.b.logging" t) (insert "\n"))
# (progn (forward-line 1) (snip-insert-mode "py.b.ordereddict" t) (insert "\n"))
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
    old_hlr = hlr
    if level == 0:
        hlr = hlssr
    elif level == 1:
        hlr = hlsr
    else:
        hlr = hlcr
    return old_hlr

def hl_lvl_reset(old_hlr):                                         # |:fnc:|
    global hlr
    hlr = old_hlr

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

class TO(object):
    pass

class TOG(object):
    def __getstate__(self):
        return {}
    pass

# --------------------------------------------------
# |||:sec:||| Current pymongo State with C extension active
# --------------------------------------------------

def expand_value(value):                               # ||:fnc:||
    """Full document expansion.

    This has to be done for current pymongo, if the C-extension is
    active. since :meth:`BSON.encode` does not provide any hooks :(.

    And when it is fully expanded, BSON travels along the same path
    again ..."""

    if hasattr(value, '_pjm_asDict'):
        return value._pjm_asDict()
    if hasattr(value, '__getstate_all__'):
        return value.__getstate_all__()
    if hasattr(value, '__getstate__'):
        st = value.__getstate__()
        if issequence(st, or_dict=True):
            return expand_value(st)
    if hasattr(value, 'items'):
        expanded = OrderedDict()
        for key, val in value.items():
            if val is not None:
                val = expand_value(val)
            expanded[key] = val
        return expanded
    if hasattr(value, 'iter'):
        expanded = list()
        for item in value:
            if item is not None:
                item = expand_value(item)
            expanded.append(item)
        return expanded
    # if JSON encodable, it is OK
    try:
        st = json.dumps(value)
        return value
    except Exception:
        # (t, e, tb) = sys.exc_info()
        # import traceback
        # printe(''.join(traceback.format_tb(tb)))
        # printf(sformat('{0}: {1}', t.__name__, e))
        # printf(sformat('{0}', type(tb).__name__))
        # printe('|:TRC:| json: ' + str(e))
        pass
    # if BSON encodable, it is OK
    try:
        st = bson.json_util.default(value)
        return value
    except Exception:
        # (t, e, tb) = sys.exc_info()
        # import traceback
        # printe(''.join(traceback.format_tb(tb)))
        # printf(sformat('{0}: {1}', t.__name__, e))
        # printf(sformat('{0}', type(tb).__name__))
        #printe('|:TRC:| BSON: ' + str(e))
        pass
    try:
        #printe('|:TRC:| pickling: ' + str(value))
        return { '_$pickle': pickle.dumps(value) }
    except picke.PicklingError:
        pass
    value = repr(value)
    return value

# --------------------------------------------------
# |||:sec:||| Current pymongo State without C extension active
# --------------------------------------------------

def wrap_element_to_bson(on=True):                         # ||:fnc:||
    if not on:
        try:
            bson._element_to_bson = bson.element_to_bson_orig
            delattr(bson, 'element_to_bson_orig')
        except AttributeError:
            pass
        return

    try:
        bson.element_to_bson_orig
    except AttributeError:
        bson.element_to_bson_orig = bson._element_to_bson

    def element_to_bson_wrapper(key, value, *args):        # ||:fnc:||
        '''This is a slightly less ugly solution, if enable_c() is provided.

        If first encoding fails, try __getstate__/pickle, then encode again.
        '''
        try:
            return bson.element_to_bson_orig(key, value, *args)
        except bson.errors.InvalidDocument:
            pass
        value = getstate_default(value)
        return bson.element_to_bson_orig(key, value, *args)

    bson._element_to_bson = element_to_bson_wrapper

# --------------------------------------------------
# |||:sec:||| Simple get_element_state/default
# --------------------------------------------------

def getstate_default(value):                               # ||:fnc:||
    #printe('|:TRC:| getstate_default')
    if not have_enable_getstate or not bc.is_getstate_enabled():
        try:
            dct = value.__getstate__()
            if isinstance(dct, dict):
                return dct
        except AttributeError:
            pass
    # try:
    #     dct = value.__dict__
    #     if isinstance(dct, dict):
    #         return dct
    # except AttributeError:
    #     pass
    try:
        return { '_$pickle' : pickle.dumps(value) }
    except pickle.PicklingError:
        return repr(value)
    # never reached
    #bson.default(value)

# --------------------------------------------------
# |||:sec:||| BSON setup
# --------------------------------------------------

def bson_reset():                                          # ||:fnc:||
    try:
        bson.enable_getstate(False)
    except:
        pass
    try:
        bson.enable_c(True)
    except:
        pass
    wrap_element_to_bson(False)

def bson_setup(enable_getstate, enable_c, get_element_state): # ||:fnc:||
    global have_enable_getstate, have_enable_c, have_get_element_state
    bson_reset()

    have_get_element_state = bc.have_get_element_state and get_element_state
    have_enable_c = bc.have_enable_c and enable_c
    have_enable_getstate = bc.have_enable_getstate and enable_getstate

    if have_enable_getstate:
        bson.enable_getstate(True)

    if not have_get_element_state:
        if not bson.has_c() or have_enable_c:
            if have_enable_c:
                bson.enable_c(False)
            wrap_element_to_bson(True)

# --------------------------------------------------
# |||:sec:||| Generic BSON encoder
# --------------------------------------------------

def bson_encode(document, check_keys=False, uuid_subtype=bson.OLD_UUID_SUBTYPE, default=None): # ||:fnc:||
    if have_get_element_state:
        return bson.BSON.encode(document, check_keys, uuid_subtype, default=default)
    if have_enable_c:
        return bson.BSON.encode(document, check_keys, uuid_subtype)
    try:
        # Try the fast one
        #printe('|:TRC:| NOT expand_value')
        encoded = bson.BSON.encode(document, check_keys, uuid_subtype)
    except bson.errors.InvalidDocument:
        # Must use the slow one
        # (t, e, tb) = sys.exc_info()
        # import traceback
        # printe(''.join(traceback.format_tb(tb)))
        # printf(sformat('{0}: {1}', t.__name__, e))
        # printf(sformat('{0}', type(tb).__name__))
        #printe('|:TRC:| expand_value')
        encoded = bson.BSON.encode(expand_value(document), check_keys, uuid_subtype)
    return encoded

def run(parameters, pass_opts):                            # ||:fnc:||
    """Application runner, when called as __main__."""

    # (progn (forward-line 1) (snip-insert-mode "py.bf.sql.ws" t) (insert "\n"))
    # (progn (forward-line 1) (snip-insert-mode "py.bf.file.arg.loop" t) (insert "\n"))

    from bson import _cbson

    printe(sformat(
        "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
        dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'has_c', bson.has_c()))

    bc.enable_dict()

    def encode_dict_test(d, default=None):
        if have_enable_c:
            bson.enable_c(False)
        check_python = not bc.is_c_enabled()

        if check_python:
            try:
                dp = bson_encode(d, default=default).decode(as_class=OrderedDict)
                printe(sformat(
                    "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                    dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'Python can do', dp))
            except bson.errors.InvalidDocument:
                (t, e, tb) = sys.exc_info()
                # import traceback
                # printe(''.join(traceback.format_tb(tb)))
                # printf(sformat('{0}: {1}', t.__name__, e))
                # printf(sformat('{0}', type(tb).__name__))
                printe(sformat(
                    "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                    dbg_comm, dbg_twid, dbg_fwid, ':ERR:', 'Python cannot do', e))

        if have_enable_c:
            bson.enable_c(True)
        check_c = bc.is_c_enabled()

        if check_c:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dc = bson_encode(d, default=default).decode(as_class=OrderedDict)
                printe(sformat(
                    "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                    dbg_comm, dbg_twid, dbg_fwid, ':DBG:', 'C      can do', dc))
            except bson.errors.InvalidDocument:
                (t, e, tb) = sys.exc_info()
                # import traceback
                # printe(''.join(traceback.format_tb(tb)))
                # printf(sformat('{0}: {1}', t.__name__, e))
                # printf(sformat('{0}', type(tb).__name__))
                printe(sformat(
                    "{0}{3:^{1}} {4:<{2}s}: ]{5!s}[",
                    dbg_comm, dbg_twid, dbg_fwid, ':ERR:', 'C      cannot do', e))

    d = OrderedDict([("one", 1), ("two", 2), ("three", 3), ("four", 4), ('objg', TOG())])

    def fmt_kwargs(kwargs):
        rep = []
        for key, val in kwargs.items():
            rep.append(key + '=' + repr(val))
        return ', '.join(rep)

    def test_run(d, lvl=0):

        hl_lvl(lvl)

        kwargs = OrderedDict([('enable_getstate', False), ('enable_c', False), ('get_element_state', False)])
        hl(fmt_kwargs(kwargs))
        bson_setup(**kwargs)
        encode_dict_test(d, default=getstate_default)

        kwargs = OrderedDict([('enable_getstate', False), ('enable_c', True), ('get_element_state', False)])
        hl(fmt_kwargs(kwargs))
        bson_setup(**kwargs)
        encode_dict_test(d, default=getstate_default)

        kwargs = OrderedDict([('enable_getstate', True), ('enable_c', True), ('get_element_state', False)])
        hl(fmt_kwargs(kwargs))
        bson_setup(**kwargs)
        encode_dict_test(d, default=getstate_default)

        kwargs = OrderedDict([('enable_getstate', False), ('enable_c', True), ('get_element_state', True)])
        hl(fmt_kwargs(kwargs))
        bson_setup(**kwargs)
        encode_dict_test(d, default=getstate_default)

        kwargs = OrderedDict([('enable_getstate', True), ('enable_c', True), ('get_element_state', True)])
        hl(fmt_kwargs(kwargs))
        bson_setup(**kwargs)
        encode_dict_test(d, default=getstate_default)
        hl_lvl(lvl+1)

    hl_lvl(1)
    hl('No pickle object')
    test_run(d)

    hl_lvl(1)
    hl('One pickle object')
    d['obj'] = TO()
    test_run(d)

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
