# Copyright 2009-2012 10gen, Inc.
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

"""BSON (Binary JSON) encoding and decoding.
"""

import calendar
import datetime
import re
import struct
import sys

from bson.binary import Binary, OLD_UUID_SUBTYPE
from bson.code import Code
from bson.dbref import DBRef
from bson.errors import (InvalidBSON,
                         InvalidDocument,
                         InvalidStringData)
from bson.max_key import MaxKey
from bson.min_key import MinKey
from bson.objectid import ObjectId
from bson.py3compat import b, binary_type
from bson.son import SON
from bson.timestamp import Timestamp
from bson.tz_util import utc

# |:sec:| Context Access Functions for _cbson
# _cbson must have access to the following functions, when it imports bson.
def default(value):
    '''Yes, it is a terrible name :)

    The C extension imports it as `get_element_state`.'''
    return _ctx.get_element_state(value)

def is_getstate_enabled():
    return _ctx.enable_getstate

def is_dict_enabled():
    return _ctx.enable_dict

def is_annotate_enabled():
    return _ctx.enable_annotate

def annotate_key():
    return _ctx.annotate_key

def is_wrap_enabled():
    return _ctx.enable_wrap

def wrap_class_key():
    return _ctx.wrap_class_key

def wrap_state_key():
    return _ctx.wrap_state_key

# |:sec:| End of Context Access Functions for _cbson

try:
    from bson import _cbson
    _use_c = True
except ImportError:
    _use_c = False

try:
    import uuid
    _use_uuid = True
except ImportError:
    _use_uuid = False

PY3 = sys.version_info[0] == 3

# This sort of sucks, but seems to be as good as it gets...
RE_TYPE = type(re.compile(""))

MAX_INT32 = 2147483647
MIN_INT32 = -2147483648
MAX_INT64 = 9223372036854775807
MIN_INT64 = -9223372036854775808

EPOCH_AWARE = datetime.datetime.fromtimestamp(0, utc)
EPOCH_NAIVE = datetime.datetime.utcfromtimestamp(0)

# Create constants compatible with all versions of
# python from 2.4 forward. In 2.x b("foo") is just
# "foo". In 3.x it becomes b"foo".
EMPTY = b("")
ZERO  = b("\x00")
ONE   = b("\x01")

BSONNUM = b("\x01") # Floating point
BSONSTR = b("\x02") # UTF-8 string
BSONOBJ = b("\x03") # Embedded document
BSONARR = b("\x04") # Array
BSONBIN = b("\x05") # Binary
BSONUND = b("\x06") # Undefined
BSONOID = b("\x07") # ObjectId
BSONBOO = b("\x08") # Boolean
BSONDAT = b("\x09") # UTC Datetime
BSONNUL = b("\x0A") # Null
BSONRGX = b("\x0B") # Regex
BSONREF = b("\x0C") # DBRef
BSONCOD = b("\x0D") # Javascript code
BSONSYM = b("\x0E") # Symbol
BSONCWS = b("\x0F") # Javascript code with scope
BSONINT = b("\x10") # 32bit int
BSONTIM = b("\x11") # Timestamp
BSONLON = b("\x12") # 64bit int
BSONMIN = b("\xFF") # Min key
BSONMAX = b("\x7F") # Max key

# |:sec:| Feature Context
# Allow different threads to have independent configurations
# E.g., enable/disable C extension independently
import threading
class _Ctx(object):
    _attrib_ = list()

    def __getstate__(self):
        state = {}
        for attr in self._attrib_:
            state[attr] = getattr(self, attr)
        return state

    def __setstate__(self, state):
        for attr, value in state.iteritems():
            setattr(self, attr, value)

class _CtxT(threading.local):
    def __setstate__(self, state):
        for attr, value in state.iteritems():
            setattr(self, attr, value)

    def __init__(self):
        self.__setstate__(_global_ctx.__getstate__())

    def setDefault(self, attr, value):
        if attr not in _global_ctx._attrib_:
            _global_ctx._attrib_.append(attr)
        setattr(self, attr, value)
        setattr(_global_ctx, attr, value)

_global_ctx = _Ctx()
_ctx = _global_ctx
_thread_ctx = _CtxT()

# |:sec:| Threading Support
def enable_threading(on=True):
    '''If threading is disabled once, it can no longer be enabled.'''
    global _ctx, _can_enable_threading
    if _can_enable_threading:
        if on:
            if not is_threading_enabled():
                _ctx = _thread_ctx
        else:
            _ctx = _global_ctx
            _can_enable_threading = False
_can_enable_threading = True

def is_threading_enabled():
    return (_ctx == _thread_ctx)

# |:sec:| Switch between C extension and pure Python
if _use_c:
    _thread_ctx.setDefault('_use_c_encoding', True)
    _thread_ctx.setDefault('_use_c_decoding', True)
else:
    _thread_ctx.setDefault('_use_c_encoding', False)
    _thread_ctx.setDefault('_use_c_decoding', False)

_function_alternatives = [
    [],                                 # encoding
    [],                                 # decoding
    ]

def _register_encoding_alternative(name, python, c):
    _function_alternatives[0].append((name, python, c))

def _register_decoding_alternative(name, python, c):
    _function_alternatives[1].append((name, python, c))

def _enable_function_alternatives(alternatives, on=True):
    '''Return False, for Python variants, True for C variants.'''
    if on and not _use_c:
        return False
    indx = 2 if on else 1
    for alternative in alternatives:
        setattr(_ctx, alternative[0], alternative[indx])
    return on

def enable_c_encoding(on=True):
    '''Enable/disable C extension for encoding.'''
    _ctx._use_c_encoding = _enable_function_alternatives(_function_alternatives[0], on)
    return _ctx._use_c_encoding

def enable_c_decoding(on=None):
    '''Enable/disable C extension for decoding.'''
    _ctx._use_c_decoding = _enable_function_alternatives(_function_alternatives[1], on)
    return _ctx._use_c_decoding

def enable_c(on=True):
    '''Enable/disable C extension for encoding/decoding.'''
    enable_c_encoding(on)
    enable_c_decoding(on)
    return _ctx._use_c_encoding and _ctx._use_c_decoding

# |:sec:| Default Callback to Get Element State
# This function is called by :func:`default`.
def _get_element_state(value):
    raise InvalidDocument("cannot convert value of type %s to bson" %
                          type(value))
_thread_ctx.setDefault('get_element_state', _get_element_state)

# |:sec:| Automatic Object Encoding Features
def enable_getstate(on=True):
    '''Enable/disable calling :meth:`__getstate__` for objects.'''
    # Make sure, these are boolean values
    _ctx.enable_getstate = (True if on else False)
_thread_ctx.setDefault('enable_getstate', False)

def enable_dict(on=True):
    '''Enable/disable getting :attr:`__dict__` for objects.'''
    _ctx.enable_dict = (True if on else False)
_thread_ctx.setDefault('enable_dict', False)

def enable_annotate(on=True):
    '''Enable/disable annotation of automatic object state with class name.

    When enabled, the state derived from :meth:`__getstate__` or
    :attr:`__dict__` is annotated unconditionally with the class name.
    The string returned by :func:`annotate_key()` is used as key.

    The key name can be set with :func:`set_annotate_key`.

    See also :func:`enable_getstate` and :func:`enable_dict`.
    '''
    _ctx.enable_annotate = (True if on else False)
_thread_ctx.setDefault('enable_annotate', False)

def set_annotate_key(key):
    '''Set key name for :func:`annotate_key`.'''
    _ctx.annotate_key = key
_thread_ctx.setDefault('annotate_key', '_$class')

def enable_wrap(on=True):
    '''Enable/disable wrapping of automatic object state.

    When enabled, the state derived from :meth:`__getstate__` or
    :attr:`__dict__` is wrapped in a :class:`dict`.

    The class name is assigned to the key returned by returned by
    :func:`wrap_class_key()`.

    The state is assigned to the key returned by returned by
    :func:`wrap_state_key()`.

    The key names can be set with :func:`set_wrap_class_key` and
    :func:`set_wrap_state_key`.

    See also :func:`enable_getstate` and :func:`enable_dict`.
    '''
    _ctx.enable_wrap = (True if on else False)
_thread_ctx.setDefault('enable_wrap', False)

def set_wrap_class_key(key):
    '''Set key name for :func:`wrap_class_key`.'''
    _ctx.wrap_class_key = key
_thread_ctx.setDefault('wrap_class_key', '_$class')

def set_wrap_state_key(key):
    '''Set key name for :func:`wrap_state_key`.'''
    _ctx.wrap_state_key = key
_thread_ctx.setDefault('wrap_state_key', '_$state')
# |:sec:| End of Features

def _get_int(data, position, as_class=None, tz_aware=False, unsigned=False):
    format = unsigned and "I" or "i"
    try:
        value = struct.unpack("<%s" % format, data[position:position + 4])[0]
    except struct.error:
        raise InvalidBSON()
    position += 4
    return value, position

def _get_c_string(data, position, length=None):
    if length is None:
        try:
            end = data.index(ZERO, position)
        except ValueError:
            raise InvalidBSON()
    else:
        end = position + length
    value = data[position:end].decode("utf-8")
    position = end + 1

    return value, position

try:
    uc_type = unicode
except NameError:
    uc_type = str

def _make_c_string(string, check_null=False):
    if isinstance(string, uc_type):
        if check_null and "\x00" in string:
            raise InvalidDocument("BSON keys / regex patterns must not "
                                  "contain a NULL character")
        return string.encode("utf-8") + ZERO
    else:
        if check_null and ZERO in string:
            raise InvalidDocument("BSON keys / regex patterns must not "
                                  "contain a NULL character")
        try:
            string.decode("utf-8")
            return string + ZERO
        except UnicodeError:
            raise InvalidStringData("strings in documents must be valid "
                                    "UTF-8: %r" % string)

def _get_number(data, position, as_class, tz_aware):
    num = struct.unpack("<d", data[position:position + 8])[0]
    position += 8
    return num, position

def _get_string(data, position, as_class, tz_aware):
    length = struct.unpack("<i", data[position:position + 4])[0] - 1
    position += 4
    return _get_c_string(data, position, length)

def _get_object(data, position, as_class, tz_aware):
    obj_size = struct.unpack("<i", data[position:position + 4])[0]
    encoded = data[position + 4:position + obj_size - 1]
    object = _elements_to_dict(encoded, as_class, tz_aware)
    position += obj_size
    if "$ref" in object:
        return (DBRef(object.pop("$ref"), object.pop("$id"),
                      object.pop("$db", None), object), position)
    return object, position

def _get_array(data, position, as_class, tz_aware):
    obj, position = _get_object(data, position, as_class, tz_aware)
    result = []
    i = 0
    while True:
        try:
            result.append(obj[str(i)])
            i += 1
        except KeyError:
            break
    return result, position

def _get_binary(data, position, as_class, tz_aware):
    length, position = _get_int(data, position)
    subtype = ord(data[position:position + 1])
    position += 1
    if subtype == 2:
        length2, position = _get_int(data, position)
        if length2 != length - 4:
            raise InvalidBSON("invalid binary (st 2) - lengths don't match!")
        length = length2
    if subtype in (3, 4) and _use_uuid:
        value = uuid.UUID(bytes=data[position:position + length])
        position += length
        return (value, position)
    # Python3 special case. Decode subtype 0 to 'bytes'.
    if PY3 and subtype == 0:
        value = data[position:position + length]
    else:
        value = Binary(data[position:position + length], subtype)
    position += length
    return value, position

def _get_oid(data, position, as_class, tz_aware):
    value = ObjectId(data[position:position + 12])
    position += 12
    return value, position

def _get_boolean(data, position, as_class, tz_aware):
    value = data[position:position + 1] == ONE
    position += 1
    return value, position

def _get_date(data, position, as_class, tz_aware):
    seconds = float(struct.unpack("<q", data[position:position + 8])[0]) / 1000.0
    position += 8
    if tz_aware:
        return EPOCH_AWARE + datetime.timedelta(seconds=seconds), position
    return EPOCH_NAIVE + datetime.timedelta(seconds=seconds), position

def _get_code(data, position, as_class, tz_aware):
    code, position = _get_string(data, position, as_class, tz_aware)
    return Code(code), position

def _get_code_w_scope(data, position, as_class, tz_aware):
    _, position = _get_int(data, position)
    code, position = _get_string(data, position, as_class, tz_aware)
    scope, position = _get_object(data, position, as_class, tz_aware)
    return Code(code, scope), position

def _get_null(data, position, as_class, tz_aware):
    return None, position

def _get_regex(data, position, as_class, tz_aware):
    pattern, position = _get_c_string(data, position)
    bson_flags, position = _get_c_string(data, position)
    flags = 0
    if "i" in bson_flags:
        flags |= re.IGNORECASE
    if "l" in bson_flags:
        flags |= re.LOCALE
    if "m" in bson_flags:
        flags |= re.MULTILINE
    if "s" in bson_flags:
        flags |= re.DOTALL
    if "u" in bson_flags:
        flags |= re.UNICODE
    if "x" in bson_flags:
        flags |= re.VERBOSE
    return re.compile(pattern, flags), position

def _get_ref(data, position, as_class, tz_aware):
    position += 4
    collection, position = _get_c_string(data, position)
    oid, position = _get_oid(data, position)
    return DBRef(collection, oid), position

def _get_timestamp(data, position, as_class, tz_aware):
    inc, position = _get_int(data, position, unsigned=True)
    timestamp, position = _get_int(data, position, unsigned=True)
    return Timestamp(timestamp, inc), position

def _get_long(data, position, as_class, tz_aware):
    # Have to cast to long; on 32-bit unpack may return an int.
    # 2to3 will change long to int. That's fine since long doesn't
    # exist in python3.
    value = long(struct.unpack("<q", data[position:position + 8])[0])
    position += 8
    return value, position

_element_getter = {
    BSONNUM: _get_number,
    BSONSTR: _get_string,
    BSONOBJ: _get_object,
    BSONARR: _get_array,
    BSONBIN: _get_binary,
    BSONUND: _get_null,  # undefined
    BSONOID: _get_oid,
    BSONBOO: _get_boolean,
    BSONDAT: _get_date,
    BSONNUL: _get_null,
    BSONRGX: _get_regex,
    BSONREF: _get_ref,
    BSONCOD: _get_code,  # code
    BSONSYM: _get_string,  # symbol
    BSONCWS: _get_code_w_scope,
    BSONINT: _get_int,  # number_int
    BSONTIM: _get_timestamp,
    BSONLON: _get_long, # Same as _get_int after 2to3 runs.
    BSONMIN: lambda w, x, y, z: (MinKey(), x),
    BSONMAX: lambda w, x, y, z: (MaxKey(), x)}

def _element_to_dict(data, position, as_class, tz_aware):
    element_type = data[position:position + 1]
    position += 1
    element_name, position = _get_c_string(data, position)
    value, position = _element_getter[element_type](data, position,
                                                    as_class, tz_aware)
    return element_name, value, position

def _elements_to_dict(data, as_class, tz_aware):
    result = as_class()
    position = 0
    end = len(data) - 1
    while position < end:
        (key, value, position) = _element_to_dict(data, position, as_class, tz_aware)
        result[key] = value
    return result

def _bson_to_dict(data, as_class, tz_aware):
    obj_size = struct.unpack("<i", data[:4])[0]
    if len(data) < obj_size:
        raise InvalidBSON("objsize too large")
    if data[obj_size - 1:obj_size] != ZERO:
        raise InvalidBSON("bad eoo")
    elements = data[4:obj_size - 1]
    return (_elements_to_dict(elements, as_class, tz_aware), data[obj_size:])
if _use_c:
    _register_decoding_alternative('_bson_to_dict', _bson_to_dict, _cbson._bson_to_dict)
    _thread_ctx.setDefault('_bson_to_dict', _cbson._bson_to_dict)
else:
    _thread_ctx.setDefault('_bson_to_dict', _bson_to_dict)

def _annotate_element_state(element, state, class_key=None):
    if not is_annotate_enabled():
        return state
    if class_key is None:
        class_key = annotate_class_key()
    if class_key is not None:
        try:
            state[class_key] = element.__class__.__name__
        except AttributeError:
            pass
    return state

def _wrap_element_state(element, state, class_key=None, state_key=None):
    if not is_wrap_enabled():
        return state
    if state_key is None:
        state_key = wrap_state_key()
    if state_key is None:
        return state
    _wrapped = {}
    if class_key is None:
        class_key = wrap_class_key()
    if class_key is not None:
        try:
            _wrapped[class_key] = element.__class__.__name__
        except AttributeError:
            pass
    _wrapped[state_key] = state
    return _wrapped

def isstring(obj):
    return isinstance(obj, basestring)
try:
    isstring("")
except NameError:
    def isstring(obj):
        return isinstance(obj, str) or isinstance(obj, bytes)

def _element_to_state(value, get_element_state=None, ensure_dict=False):
    if is_getstate_enabled():
        try:
            state = value.__getstate__()
        except AttributeError:
            pass
        else:
            if isinstance(state, dict):
                _annotate_element_state(value, state)
                return state

    if get_element_state is None:
        get_element_state = default
    try:
        state = get_element_state(value)
    except InvalidDocument:
        pass
    else:
        if not ensure_dict or isinstance(state, dict):
            return state

    if is_dict_enabled():
        try:
            state = value.__dict__
        except AttributeError:
            pass
        else:
            if isinstance(state, dict):
                _annotate_element_state(value, state)
                return state
            
    # This raises an exception and should never be overloaded
    return _get_element_state(value)

def _element_to_bson(key, value, check_keys, uuid_subtype, get_element_state=None):
    if not isstring(key):
        raise InvalidDocument("documents must have only string keys, "
                              "key was %r" % key)

    if check_keys:
        if key.startswith("$"):
            raise InvalidDocument("key %r must not start with '$'" % key)
        if "." in key:
            raise InvalidDocument("key %r must not contain '.'" % key)

    name = _make_c_string(key, True)
    if isinstance(value, float):
        return BSONNUM + name + struct.pack("<d", value)

    if _use_uuid:
        if isinstance(value, uuid.UUID):
            # Python 3.0(.1) returns a bytearray instance for bytes (3.1 and
            # newer just return a bytes instance). Convert that to binary_type
            # for compatibility.
            value = Binary(binary_type(value.bytes), subtype=uuid_subtype)

    if isinstance(value, Binary):
        subtype = value.subtype
        if subtype == 2:
            value = struct.pack("<i", len(value)) + value
        return (BSONBIN + name +
                struct.pack("<i", len(value)) + b(chr(subtype)) + value)
    if isinstance(value, Code):
        cstring = _make_c_string(value)
        if not value.scope:
            length = struct.pack("<i", len(cstring))
            return BSONCOD + name + length + cstring
        scope = _ctx._dict_to_bson(value.scope, False, uuid_subtype, False, get_element_state)
        full_length = struct.pack("<i", 8 + len(cstring) + len(scope))
        length = struct.pack("<i", len(cstring))
        return BSONCWS + name + full_length + length + cstring + scope
    if isinstance(value, binary_type):
        if PY3:
            # Python3 special case. Store 'bytes' as BSON binary subtype 0.
            return (BSONBIN + name +
                    struct.pack("<i", len(value)) + ZERO + value)
        cstring = _make_c_string(value)
        length = struct.pack("<i", len(cstring))
        return BSONSTR + name + length + cstring
    if isinstance(value, uc_type):
        cstring = _make_c_string(value)
        length = struct.pack("<i", len(cstring))
        return BSONSTR + name + length + cstring
    if isinstance(value, dict):
        return BSONOBJ + name + _ctx._dict_to_bson(value, check_keys, uuid_subtype, False, get_element_state)
    if isinstance(value, (list, tuple)):
        as_dict = SON(zip([str(i) for i in range(len(value))], value))
        return BSONARR + name + _ctx._dict_to_bson(as_dict, check_keys, uuid_subtype, False, get_element_state)
    if isinstance(value, ObjectId):
        return BSONOID + name + value.binary
    if value is True:
        return BSONBOO + name + ONE
    if value is False:
        return BSONBOO + name + ZERO
    if isinstance(value, int):
        # TODO this is an ugly way to check for this...
        if value > MAX_INT64 or value < MIN_INT64:
            raise OverflowError("BSON can only handle up to 8-byte ints")
        if value > MAX_INT32 or value < MIN_INT32:
            return BSONLON + name + struct.pack("<q", value)
        return BSONINT + name + struct.pack("<i", value)
    # 2to3 will convert long to int here since there is no long in python3.
    # That's OK. The previous if block will match instead.
    if isinstance(value, long):
        if value > MAX_INT64 or value < MIN_INT64:
            raise OverflowError("BSON can only handle up to 8-byte ints")
        return BSONLON + name + struct.pack("<q", value)
    if isinstance(value, datetime.datetime):
        if value.utcoffset() is not None:
            value = value - value.utcoffset()
        millis = int(calendar.timegm(value.timetuple()) * 1000 +
                     value.microsecond / 1000)
        return BSONDAT + name + struct.pack("<q", millis)
    if isinstance(value, Timestamp):
        time = struct.pack("<I", value.time)
        inc = struct.pack("<I", value.inc)
        return BSONTIM + name + inc + time
    if value is None:
        return BSONNUL + name
    if isinstance(value, RE_TYPE):
        pattern = value.pattern
        flags = ""
        if value.flags & re.IGNORECASE:
            flags += "i"
        if value.flags & re.LOCALE:
            flags += "l"
        if value.flags & re.MULTILINE:
            flags += "m"
        if value.flags & re.DOTALL:
            flags += "s"
        if value.flags & re.UNICODE:
            flags += "u"
        if value.flags & re.VERBOSE:
            flags += "x"
        return BSONRGX + name + _make_c_string(pattern, True) + \
            _make_c_string(flags)
    if isinstance(value, DBRef):
        return _element_to_bson(key, value.as_doc(), False, uuid_subtype, get_element_state)
    if isinstance(value, MinKey):
        return BSONMIN + name
    if isinstance(value, MaxKey):
        return BSONMAX + name

    return _element_to_bson(key, _element_to_state(value), check_keys, uuid_subtype, get_element_state)

# Contrary to the C implementation, the Python
# implementation of :func:`_dict_to_bson` does not check
# `document` for an explicit dict type and accepts any
# object that implements key access and :meth:`iteritems`.
#
# Although this is really the better behavior, this check makes
# sure, that both implementations act identically.
dict_to_bson_ensure_c_compat = True

def _dict_to_bson(dct, check_keys, uuid_subtype, top_level=True, get_element_state=None):
    if dict_to_bson_ensure_c_compat and not isinstance(dct, dict):
        try:
            dct = _element_to_state(dct, ensure_dict=True)
        except InvalidDocument:
            # ensure that test_arbitrary_mapping_encode passes
            raise TypeError("encoder expected a mapping type but got: %r" % dct)

    try:
        elements = []
        if top_level and "_id" in dct:
            elements.append(_element_to_bson("_id", dct["_id"], False, uuid_subtype, get_element_state))
        for (key, value) in dct.iteritems():
            if not top_level or key != "_id":
                elements.append(_element_to_bson(key, value, check_keys, uuid_subtype, get_element_state))
    except AttributeError:
        raise TypeError("encoder expected a mapping type but got: %r" % dct)

    encoded = EMPTY.join(elements)
    length = len(encoded) + 5
    return struct.pack("<i", length) + encoded + ZERO
if _use_c:
    _register_encoding_alternative('_dict_to_bson', _dict_to_bson, _cbson._dict_to_bson)
    _thread_ctx.setDefault('_dict_to_bson', _cbson._dict_to_bson)
else:
    _thread_ctx.setDefault('_dict_to_bson', _dict_to_bson)

def decode_all(data, as_class=dict, tz_aware=True):
    """Decode BSON data to multiple documents.

    `data` must be a string of concatenated, valid, BSON-encoded
    documents.

    :Parameters:
      - `data`: BSON data
      - `as_class` (optional): the class to use for the resulting
        documents
      - `tz_aware` (optional): if ``True``, return timezone-aware
        :class:`~datetime.datetime` instances

    .. versionadded:: 1.9
    """
    docs = []
    position = 0
    end = len(data) - 1
    while position < end:
        obj_size = struct.unpack("<i", data[position:position + 4])[0]
        if len(data) - position < obj_size:
            raise InvalidBSON("objsize too large")
        if data[position + obj_size - 1:position + obj_size] != ZERO:
            raise InvalidBSON("bad eoo")
        elements = data[position + 4:position + obj_size - 1]
        position += obj_size
        docs.append(_elements_to_dict(elements, as_class, tz_aware))
    return docs
if _use_c:
    _register_decoding_alternative('decode_all', decode_all, _cbson.decode_all)
    _thread_ctx.setDefault('decode_all', _cbson.decode_all)
else:
    _thread_ctx.setDefault('decode_all', decode_all)

def is_valid(bson):
    """Check that the given string represents valid :class:`BSON` data.

    Raises :class:`TypeError` if `bson` is not an instance of
    :class:`str` (:class:`bytes` in python 3). Returns ``True``
    if `bson` is valid :class:`BSON`, ``False`` otherwise.

    :Parameters:
      - `bson`: the data to be validated
    """
    if not isinstance(bson, binary_type):
        raise TypeError("BSON data must be an instance "
                        "of a subclass of %s" % (binary_type.__name__,))

    try:
        (_, remainder) = _ctx._bson_to_dict(bson, dict, True)
        return remainder == EMPTY
    except:
        return False

class BSON(binary_type):
    """BSON (Binary JSON) data.
    """

    @classmethod
    def encode(cls, document, check_keys=False, uuid_subtype=OLD_UUID_SUBTYPE, default=None):
        """Encode a document to a new :class:`BSON` instance.

        A document can be any mapping type (like :class:`dict`).

        Raises :class:`TypeError` if `document` is not a mapping type,
        or contains keys that are not instances of
        :class:`basestring` (:class:`str` in python 3). Raises
        :class:`~bson.errors.InvalidDocument` if `document` cannot be
        converted to :class:`BSON`.

        :Parameters:
          - `document`: mapping type representing a document
          - `check_keys` (optional): check if keys start with '$' or
            contain '.', raising :class:`~bson.errors.InvalidDocument` in
            either case

        .. versionadded:: 1.9
        """
        return cls(_ctx._dict_to_bson(document, check_keys, uuid_subtype, get_element_state=default))

    def decode(self, as_class=dict, tz_aware=False):
        """Decode this BSON data.

        The default type to use for the resultant document is
        :class:`dict`. Any other class that supports
        :meth:`__setitem__` can be used instead by passing it as the
        `as_class` parameter.

        If `tz_aware` is ``True`` (recommended), any
        :class:`~datetime.datetime` instances returned will be
        timezone-aware, with their timezone set to
        :attr:`bson.tz_util.utc`. Otherwise (default), all
        :class:`~datetime.datetime` instances will be naive (but
        contain UTC).

        :Parameters:
          - `as_class` (optional): the class to use for the resulting
            document
          - `tz_aware` (optional): if ``True``, return timezone-aware
            :class:`~datetime.datetime` instances

        .. versionadded:: 1.9
        """
        (document, _) = _ctx._bson_to_dict(self, as_class, tz_aware)
        return document

def has_c():
    """Is the C extension installed?

    .. versionadded:: 1.9
    """
    return _use_c
