# -*- coding: utf-8 -*-
# Copyright (C) 2012, Wolfgang Scherer, <Wolfgang.Scherer at gmx.de>
# Sponsored by WIEDENMANN SEILE GMBH, http://www.wiedenmannseile.de
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bson
from bson.son import SON
from bson.errors import InvalidConfiguration

__all__ = [
    'Context',
    'ThreadContext',
    'get_context',
    'set_context',
    '_update_thread_context',
    'enable_threading',
    'is_threading_enabled',
    'lock',
    'unlock',
    ]

_can_enable_threading = True

# |:sec:| Feature Context
# Allow different threads to have independent configurations
# E.g., enable/disable C extension independently
import threading
import copy
class Context(object):                                     # ||:cls:||
    '''BSON encoding/decoding configuration context.

    .. versionadded:: 2.2.1-fork
    '''
    # class attributes
    _attrib_ = list()
    _defaults_ = SON((
        # instance configuration values
        ('_use_c_encoding', True),
        ('_use_c_decoding', True),
        # function alternatives BSON C extension/Python
        ('_dict_to_bson', None),
        ('_bson_to_dict', None),
        ('decode_all', None),
        # function alternatives pymongo C extension/Python
        ('_insert_message', None),
        ('_update_message', None),
        ('_query_message', None),
        ('_get_more_message', None),
        ))
    _c_functions_ = [
        [],                                 # encoding
        [],                                 # decoding
        ]

    # convenience lock
    lock = threading.RLock()

    def __init__(self):
        for attr, value in self._defaults_.iteritems():
            if attr not in self._attrib_:
                self._attrib_.append(attr)
            setattr(self, attr, copy.deepcopy(value))

    def __getitem__(self, key):
        # |:check:| this renders a borrowed reference?
        return vars(self)[key]

    def __setitem__(self, key, value):
        vars(self)[key] = value

    def __getstate__(self):
        state = {}
        self.lock.acquire()
        for attr in self._attrib_:
            state[attr] = getattr(self, attr)
        self.lock.release()
        return state

    def __setstate__(self, state):
        self.lock.acquire()
        for attr, value in state.iteritems():
            setattr(self, attr, value)
        self.lock.release()

    def _register_encoding_alternative(self, name, python, c):
        self._c_functions_[0].append((name, python, c))

    def _register_decoding_alternative(self, name, python, c):
        self._c_functions_[1].append((name, python, c))

    def _enable_c_functions_(self, alternatives, on=True):
        '''Return False for Python variants, True for C variants.'''
        if on and not bson.has_c():
            return False
        indx = 2 if on else 1
        for alternative in alternatives:
            setattr(self, alternative[0], alternative[indx])
        return (True if on else False)

    def enable_c_encoding(self, on=True):
        '''Enable/disable C extension for encoding.

        :returns: self for chaining.'''
        self._use_c_encoding = self._enable_c_functions_(self._c_functions_[0], on)
        return self

    def is_c_encoding_enabled(self):
        '''Check if C extension is enabled for decoding.'''
        return self._use_c_encoding

    def enable_c_decoding(self, on=True):
        '''Enable/disable C extension for decoding.

        :returns: self for chaining.'''
        self._use_c_decoding = self._enable_c_functions_(self._c_functions_[1], on)
        return self

    def is_c_decoding_enabled(self):
        '''Check if C extension is enabled for decoding.'''
        return self._use_c_decoding

    def enable_c(self, on=True):
        '''Enable/disable C extension for encoding/decoding.

        :returns: self for chaining.'''
        self.enable_c_encoding(on)
        self.enable_c_decoding(on)
        return self

    def is_c_enabled(self, both=False):
        '''Check if C extension is enabled for encoding and/or decoding.

        :param both: If False (the default), the C extension is considered
          enabled if it is enabled for any of the encoding or decoding
          functions.

          If True, the C extension is considered enabled if it is enabled
          for both the encoding and decoding functions.
        '''
        if both:
            return self._use_c_encoding and self._use_c_decoding
        return self._use_c_encoding or self._use_c_decoding

    def setDefault(self, attr, value):
        '''Set attribute as default.

        :returns: self for chaining.'''
        if attr not in self._attrib_:
            self._attrib_.append(attr)
        setattr(self, attr, value)
        return self

    def __str__(self):
        s = []
        for attr in self._attrib_:
            s.append("{0:<19s}: {1!s}".format( attr, self[attr]))
        return '\n'.join(s)

class ChildContext(Context):                               # ||:cls:||

    def __init__(self, default=False):
        #super(ChildContext, self).__init__()
        if default:
            _default_ctx = bson._default_ctx
            self.__setstate__(_default_ctx.__getstate__())
            self.lock = _default_ctx.lock
        else:
            _context = bson._context
            self.__setstate__(_context.__getstate__())
            self.lock = _context.lock

    def setDefault(self, attr, value):
        '''Set attribute as default.

        :returns: self for chaining.'''
        _default_ctx = bson._default_ctx
        if attr not in _default_ctx._attrib_:
            _default_ctx._attrib_.append(attr)
        setattr(_default_ctx, attr, value)
        setattr(self, attr, value)
        return self

class ThreadContext(threading.local, ChildContext):        # ||:cls:||

    def __init__(self):
        threading.local.__init__(self)
        ChildContext.__init__(self, True)
        # new thread local convenience lock
        self.lock = threading.RLock()

# |:sec:| Context
def get_context(default=False):                            # ||:fnc:||
    '''Get copy of (default) context suitable as parameter to
    encoding/decoding functions or for :func:`set_context`.'''
    return ChildContext(default)

def set_context(context, default=False):                   # ||:fnc:||
    '''Set (default) context.'''
    if default:
        _default_ctx = bson._default_ctx
        _default_ctx.__setstate__(context.__getstate__())
    else:
        _context = bson._context
        _context.__setstate__(context.__getstate__())

def _update_thread_context():
    if not is_threading_enabled():
        bson._thread_ctx.__setstate__(bson._default_ctx.__getstate__())

# |:sec:| Threading Support
def enable_threading(on=True):                             # ||:fnc:||
    '''If threading is disabled once, it can no longer be enabled.'''
    global _can_enable_threading
    if on:
        if not is_threading_enabled():
            if _can_enable_threading:
                _default_ctx = bson._default_ctx
                _thread_ctx = bson._thread_ctx
                _thread_ctx.__setstate__(_default_ctx.__getstate__())
                bson._context = _thread_ctx
            else:
                raise InvalidConfiguration('cannot enable BSON threading')
    else:
        if is_threading_enabled():
            _default_ctx = bson._default_ctx
            bson._context = _default_ctx
        _can_enable_threading = False

def is_threading_enabled():                                # ||:fnc:||
    return (bson._context == bson._thread_ctx)

def lock(default=False):                                   # ||:fnc:||
    '''Acquire the lock for the (default) context.

    :returns: (default) context copy.'''
    if default:
        _default_ctx = bson._default_ctx
        _default_ctx.lock.acquire()
    else:
        _context = bson._context
        _context.lock.acquire()
    return get_context(default)

def unlock(context=None, default=False):                   # ||:fnc:||
    '''Release the lock for the (default) context.

    :param context: if not None, set the (default) context before
      releasing the lock.'''
    if context is not None:
        set_context(context, default)
    if default:
        _default_ctx = bson._default_ctx
        _default_ctx.lock.release()
    else:
        _context = bson._context
        _context.lock.release()

# |:sec:| End of Context

# :ide: COMPILE: Run w/o args
# . (progn (save-buffer) (compile (concat "cd .. && export PYTHONPATH=\"$( pwd )\" && python " (buffer-file-name) " ")))

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
