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
'''Context support for BSON codec.

Provides runtime (de-)activation of C extensions, per-thread
context support, object conversion callbacks.

The API is imported by the :mod:`bson` module and should be
accessed there.

When module :mod:`bson` is loaded, the default :class:`Context` is
initialized with Python and C extension function vectors. After
loading, the main thread context is initialized from the default
context.

The state of the BSON module after initialization corresponds to the
default of the BSON module without the context extension. The default
context is the active context.

Thread specific context support must be be explicitely enabled with
:func:`enable_threading`. If it is disabled with
:func:`enable_threading`, it can no longer be re-enabled.

Each new thread local context is initialized from the default context.

The :func:`lock` and :func:`unlock` functions operate on the active
context.

>>> import bson
>>> sv_context = bson.lock()
>>> context = (
...     bson.get_context()
...     .enable_c(True)
...     .addHook("__bson__", True)
...     .addHook("__getstate__", True)
...     )
>>> def get_object_state(obj, need_dict):
...     try:
...         return (True, obj.__getstate__())
...     except AttributeError:
...         pass
...     return (False, None)
>>> context.get_object_state = get_object_state
>>> bson.set_context(context)
>>> bson.unlock(sv_context)
'''

import bson
from bson.son import SON
try:
    from bson.errors import InvalidConfiguration
except ImportError:
    import bson.errors
    exec('''
class InvalidConfiguration(BSONError):
    """Raised upon configuration errors.
    E.g., when threading is enabled, after it was previously disabled.
    """
    ''', vars(bson.errors))
    from bson.errors import InvalidConfiguration

__all__ = [
    'Context',
    'ThreadContext',
    'dbg_check_context',
    'dbg_check_context_required',
    'get_context',
    'set_context',
    '_update_thread_context',
    'enable_threading',
    'is_threading_enabled',
    'lock',
    'unlock',
    ]

_can_enable_threading = True

try:
    getattr(dict(), 'iteritems')
    ditems  = lambda d: getattr(d, 'iteritems')()
    dkeys   = lambda d: getattr(d, 'iterkeys')()
    dvalues = lambda d: getattr(d, 'itervalues')()
except AttributeError:
    ditems  = lambda d: getattr(d, 'items')()
    dkeys   = lambda d: getattr(d, 'keys')()
    dvalues = lambda d: getattr(d, 'values')()

# |:sec:| Feature Context
# Allow different threads to have independent configurations
# E.g., enable/disable C extension independently
import threading
import copy
class Context(object):                                     # ||:cls:||
    """BSON encoding/decoding configuration context.

    **C Extension (De-)Activation**

    Encoding/decoding functions are retrieved from :class:`Context`
    attributes. The active set of functions can be switched with
    :meth:`enable_c`, :meth:`enable_c_encoding`,
    :meth:`enable_c_decoding`. Methods :meth:`is_c_enabled`,
    :meth:`is_c_encoding_enabled`, :meth:`is_c_decoding_enabled` are
    used to determine the active function set.

    **Automatic Object Conversion**

    :attr:`object_state_hooks` holds parameters for object attributes
    that are used, when an object cannot be converted::

        [(attribute_name, dict_required), ...]

    E.g.::

        context.object_state_hooks = [('__bson__', False), ('__getstate__', True), ('__dict__', True)]

    If an object attribute is found and provides the :meth:`__call__`
    interface, it is invoked as a method, otherwise the attribute
    value is used as is.

    :attr:`get_object_state` holds a last resort callback to retrieve
    an object's state::

        valid, result = context.get_object_state(obj, need_dict)

    **Context Locking**

    The :attr:`lock` attribute is used to serialize access to the
    context. It is internally used by the :meth:`__getstate__` and
    :meth:`__setstate__` methods.

    .. versionadded:: 2.2.1-fork
    """
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

        # object_state_hooks:
        ('object_state_hooks', []),

        ('get_object_state', None),

        # document class, when context is used as `as_class` parameter
        # for decoding.
        ('as_class', SON),
        ('_pyjsmo_context_key', '_$context'),
        ))
    _c_functions_ = [
        [],                                 # encoding
        [],                                 # decoding
        ]

    # convenience lock
    lock = threading.RLock()

    def __call__(self, *args, **kwargs):
        '''Document class generator.

        This makes :class:`Context` suitable for parameter `as_class`
        of decoding functions.

        Attribute :attr:`as_class` is used as type to create a
        document object instance.

        Its constructor is called with a dict argument:

            self.as_class({self._pyjsmo_context_key: self})
        '''
        document = self.as_class({self._pyjsmo_context_key: self})
        return document

    def __init__(self, context=None):
        for attr, value in ditems(self._defaults_):
            if attr not in self._attrib_:
                self._attrib_.append(attr)
            setattr(self, attr, copy.deepcopy(value))
        if context is not None:
            self.__setstate__(context.__getstate__())

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
        for attr, value in ditems(state):
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

    def addHook(self, hook, require_dict=True):
        '''Add hook to :attr:`object_state_hooks`.

        :returns: self for chaining.'''
        oshd = SON(self.object_state_hooks)
        if hook not in oshd:
            oshd[hook] = require_dict
            self.object_state_hooks = list(oshd.items())
        return self

    def removeHook(self, hook):
        '''Remove hook from :attr:`object_state_hooks`.

        :returns: self for chaining.'''
        oshd = SON(self.object_state_hooks)
        if hook in oshd:
            del(oshd[hook])
            self.object_state_hooks = list(oshd.items())
        return self

    def enable_hook(self, on=True, hook='__getstate__', require_dict=True):
        '''Enable/disable object state hook.

        :returns: self for chaining.'''
        if on:
            self.addHook(hook, require_dict)
        else:
            self.removeHook(hook)
        return self

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
    """Thread specific context based on :class:`threading.local`."""

    def __init__(self):
        threading.local.__init__(self)
        ChildContext.__init__(self, True)
        # new thread local convenience lock
        self.lock = threading.RLock()

# |:sec:| Context debuggging
def dbg_check_context(context):         # |:debug:|
    '''bson.check_context = bson.dbg_check_context'''
    if context is None:
        return
    return dbg_check_context_required(context)

def dbg_check_context_required(context):
    '''bson.check_context = bson.dbg_check_context_required'''
    if not isinstance(context, Context):
        import traceback
        traceback.print_stack()
        raise TypeError('not a BSON context' + repr(context))

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
                if threading.active_count() > 1:
                    raise InvalidConfiguration(
                        'BSON thread support can only be enabled in main thread'
                        ' (active threads: ' + str(threading.active_count()) + ')')
                _default_ctx = bson._default_ctx
                _thread_ctx = bson._thread_ctx
                _thread_ctx.__setstate__(_default_ctx.__getstate__())
                bson._context = _thread_ctx
            else:
                raise InvalidConfiguration('BSON thread support is disabled')
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

def export_to_bson():
    '''Patch support for original BSON codec.'''
    for attr in __all__:
        if not hasattr(bson, attr):
            setattr(bson, attr, globals()[attr])
    if not hasattr(bson, '_context'):
        exec('''
_context = Context()
_default_ctx = _context
_thread_ctx = ThreadContext()
_context.setDefault('_use_c_encoding', _use_c)
_context.setDefault('_use_c_decoding', _use_c)
''', vars(bson))

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
