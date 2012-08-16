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
'''PyMongo/BSON Context Extension.

usage: import pymongo_context

- BSON encoding/decoding context
- enable/disable C extensions at runtime
- threading support (thread-local context)

Works with PyMongo driver fork at
https://github.com/wolfmanx/mongo-python-driver
'''

import sys
import ast
import copy
import pkgutil

import bson
import pymongo.message

try:
    import bson.context
    bson_context = bson.context
    must_patch = False
except ImportError:
    try:
        from pymongo_context import bson_context
    except ImportError:
        if __name__ == '__main__':
            sys.modules['pymongo_context'] = sys.modules['__main__']
        import bson_context
        sys.modules['pymongo_context.bson_context'] = bson_context
    must_patch = True

try:
    getattr(dict(), 'iteritems')
    ditems  = lambda d: getattr(d, 'iteritems')()
    dkeys   = lambda d: getattr(d, 'iterkeys')()
    dvalues = lambda d: getattr(d, 'itervalues')()
except AttributeError:
    ditems  = lambda d: getattr(d, 'items')()
    dkeys   = lambda d: getattr(d, 'keys')()
    dvalues = lambda d: getattr(d, 'values')()

# --------------------------------------------------
# |||:sec:||| Dump Utilities
# --------------------------------------------------

# (progn (forward-line 1) (snip-insert-mode "py.f.dump.object" t) (insert "\n"))
def matching_object_attribs(obj, pattern):                 # ||:fnc:||
    """List of object attributes matching pattern."""
    import re
    attribs = []
    for attr in dir(obj):
        if re.search(pattern, attr):
            attribs.append(attr)
    return attribs

def dump_dict(dct, exclude=None, include=None, as_is=False): # ||:fnc:||
    fwid = (len(globals()['dbg_comm'] if 'dbg_comm' in globals() else '# ')
            + (globals()['dbg_twid'] if 'dbg_twid' in globals() else 9)
            + (globals()['dbg_fwid'] if 'dbg_fwid' in globals() else 15)
            + 1)
    if exclude is None:
        exclude = list()
    _exclude = list(exclude)
    ditems = dct.items()
    if not as_is:
        ditems = sorted(ditems)
    for attr, value in ditems:
        if include is not None and attr not in include:
            continue
        if attr in _exclude:
            continue
        print('{1:<{0}s}: {2!r}'.format(fwid, attr, value))

def dump_object(obj, exclude=None, *args, **kwargs):       # ||:fnc:||
    if exclude is None:
        exclude = list()
    kwargs['as_is'] = kwargs.get('as_is', False)
    _exclude = list(exclude)
    _exclude.extend((
        '__builtins__',
        '__doc__',
        ))
    dump_dict(vars(obj), _exclude, *args, **kwargs)

def dump_bson():                                           # ||:fnc:||
    dump_object(bson,
                exclude=matching_object_attribs(bson, '^_element|^_to|^is_valid'),
                include=matching_object_attribs(bson, '(_dict|decode|^_py|^_context|_ctx|^enable|^is_)(?i)'))

def dump_message():                                        # ||:fnc:||
    dump_object(pymongo.message,
                #exclude=matching_object_attribs(bson, '^_element|^_to|^is_valid'),
                include=matching_object_attribs(pymongo.message, '^(get_more|insert|query|update|^_py)(?i)')
                )

# --------------------------------------------------
# |||:sec:||| Module Resource/Extract Section
# --------------------------------------------------

import os
def path_split_all(path, path_mod=None):
    if path_mod is None:
        path_mod = os.path
    parts = []
    head = path
    while True:
        head, tail = path_mod.split(head)
        if len(tail) != 0:
            part=tail
            tail = ''
        elif len(head) != 0:
            part=head
            head = ''
        else:
            part = ''
        if len(part) == 0:
            break
        parts.append(part)
    return reversed(parts)

import posixpath
def path_to_posixpath(path, with_drive=False, native_path_mod=None, fast=False):
    '''convert path to POSIX path.

    :param fast: when True, use posixpath.abspath, if native_path_mod
      == posixpath.'''
    if native_path_mod is None:
        native_path_mod = os.path
    (drive, file_path) = native_path_mod.splitdrive(path)
    if not with_drive:
        drive = ''
    parts = []
    if native_path_mod == posixpath and fast:
        parts.append(posixpath.abspath(file_path))
    else:
        for part in path_split_all(file_path, native_path_mod):
            if part == native_path_mod.sep:
                part = posixpath.sep
            if part == native_path_mod.pardir:
                parts.append(posixpath.pardir)
            elif part == native_path_mod.curdir:
                parts.append(posixpath.curdir)
            else:
                parts.append(part)
    return ''.join((drive, posixpath.join(*parts)))

# |:note:| needs path_to_posixpath
def module_resource_from_path(path, module, level=1):      # ||:fnc:||
    '''Get module resource from path to resource.

    >>> resource = module_resource_from_path(__file__, __name__)
    >>> start = resource.find("def module_resource_from_path")
    >>> if start >= 0:
    ...     end = resource[start:].find(":")
    ...     printf(resource[start:start+end+1])
    def module_resource_from_path(path, module, level=1):
    '''
    ppath = path_to_posixpath(path.replace('.pyc', '.py'))
    parts = list(path_split_all(ppath, posixpath))
    parts = parts[-level:]
    resource_location = posixpath.join(*parts)
    return pkgutil.get_data(module, resource_location)

# (progn (forward-line 1) (snip-insert-mode "py.f.extract.section" t) (insert "\n"))
import re
def extract_section(string, section_name_rx, section_tag=None, anchor_rx=None): # ||:fnc:||
    '''Extract section from string.

    >>> sections="""
    ... # |||\x3asec:||| section_name
    ... # in section section_name
    ... # |||\x3asec:||| other_section
    ... # in section other_section
    ... # |||\x3asec:|||
    ... # rest
    ... """

    >>> printf(extract_section(sections, 'section_name'))
    # |||\x3asec:||| section_name
    # in section section_name

    >>> printf(extract_section(sections, 'other_section'))
    # |||\x3asec:||| other_section
    # in section other_section

    >>> len(extract_section(sections, 'not_here')) == 0
    True
    '''
    if section_tag is None:
        section_tag = '|||' ':sec:|||'
    if anchor_rx is None:
        anchor_rx = '^#[ \t]*'
    ste = re.escape(section_tag)
    section_rx = ''.join((anchor_rx, ste))
    section_start_rx = ''.join((section_rx, '[ \t]*', section_name_rx))
    mo = re.search(section_start_rx, string, re.M)
    if mo is None:
        return ''
    section = string[mo.start(0):]
    mo = re.search(section_rx, section[1:], re.M)
    if mo is not None:
        section = section[:mo.start(0)]
    return section

# --------------------------------------------------
# |||:sec:||| AST Manipulation
# --------------------------------------------------

def map_ast_functions(                                     # ||:fnc:||
    ast_module,
    function_copy_map=None,
    function_rename_map=None,
    append=True):
    if function_copy_map is None:
        function_copy_map = dict()

    if function_rename_map is None:
        function_rename_map = dict()

    function_copy_map_done = dict()
    function_rename_map_done = dict()
    for key in function_copy_map:
        function_copy_map_done[key] = False
    for key in function_rename_map:
        function_rename_map_done[key] = False

    # Rename Python AST objects, copy Python AST objects with new name
    # (first occurence only)
    mapped_objects = list()
    for node in ast.walk(ast_module):
        if isinstance(node, ast.FunctionDef):
            if node.name in function_rename_map:
                if not function_rename_map_done[node.name]:
                    node.name = function_rename_map[node.name]
                    function_rename_map_done[node.name] = True
            if node.name in function_copy_map:
                if not function_copy_map_done[node.name]:
                    cnode = copy.deepcopy(node)
                    cnode.name = function_copy_map[node.name]
                    mapped_objects.append(cnode)
                    function_copy_map_done[node.name] = True

    # Append Python implementations to module
    if append:
        for node in mapped_objects:
            ast_module.body.append(node)

    return mapped_objects

if False:
# --------------------------------------------------
# |||:sec:||| BSON Module Patch Setup
# --------------------------------------------------
    from pymongo_context.bson_context import *
    _context = Context()
    _default_ctx = _context
    _thread_ctx = ThreadContext()
    _context.setDefault('_use_c_encoding', _use_c)
    _context.setDefault('_use_c_decoding', _use_c)
    check_context = lambda x: None

    if _use_c:
        _context._register_decoding_alternative('_bson_to_dict', _py_bson_to_dict, _cbson._bson_to_dict)
        _context.setDefault('_bson_to_dict', _cbson._bson_to_dict)
    else:
        _context.setDefault('_bson_to_dict', _py_bson_to_dict)
    def _bson_to_dict(*args, **kwargs):
        return _context._bson_to_dict(*args, **kwargs)

    if _use_c:
        _context._register_encoding_alternative('_dict_to_bson', _py_dict_to_bson, _cbson._dict_to_bson)
        _context.setDefault('_dict_to_bson', _cbson._dict_to_bson)
    else:
        _context.setDefault('_dict_to_bson', _py_dict_to_bson)
    def _dict_to_bson(dct, check_keys, uuid_subtype, top_level=True, **kwargs):
        ctx = kwargs.pop('context', None)
        ctx = _context
        try:
            return ctx._dict_to_bson(dct, check_keys, uuid_subtype, top_level)
        except TypeError:
            # C extension behaves differently see https://jira.mongodb.org/browse/PYTHON-380
            return ctx._dict_to_bson(dct, check_keys, uuid_subtype)

    if _use_c:
        _context._register_decoding_alternative('decode_all', _py_decode_all, _cbson.decode_all)
        _context.setDefault('decode_all', _cbson.decode_all)
    else:
        _context.setDefault('decode_all', _py_decode_all)
    def decode_all(*args, **kwargs):
        return _context.decode_all(*args, **kwargs)

    # wrapper around _element_to_bson to support object_state_hooks
    _context.setDefault('_element_to_bson', _element_to_bson)

    def _try_object_hooks(value, need_dict, context):
        ctx = _context
        hook_defs = ctx.object_state_hooks
        for hook_def in hook_defs:
            dict_required = need_dict or hook_def[1]
            try:
                hook = getattr(value, hook_def[0])
            except AttributeError:
                pass
            else:
                if callable(hook):
                    result = hook()
                else:
                    result = hook
                if not dict_required or isinstance(result, dict):
                    return (True, result)

        get_object_state = ctx.get_object_state
        if get_object_state is not None:
            valid, result = get_object_state(value, need_dict)
            if valid and (not need_dict or isinstance(result, dict)):
                return (True, result)

        return (False, None)

    import sys
    def _element_to_bson(key, value, *args):
        try:
            return _context._element_to_bson(key, value, *args)
        except InvalidDocument:
            (t, e, tb) = sys.exc_info()
            del(tb)
            valid, converted = _try_object_hooks(value, False, None)
            if valid:
                return _context._element_to_bson(key, converted, *args)
            raise e

    _update_thread_context()

# --------------------------------------------------
# |||:sec:||| Patch BSON Module
# --------------------------------------------------

def patch_bson(module_resource):                           # ||:fnc:||
    function_copy_map_bson = {
        '_dict_to_bson': '_py_dict_to_bson',
        '_bson_to_dict': '_py_bson_to_dict',
        'decode_all': '_py_decode_all',
        }

    # get the AST tree for module
    # use pkgutil, in case the source is in a ZIP file.
    bson_resource = pkgutil.get_data('bson', '__init__.py')
    bson_ast_module = ast.parse(bson_resource)

    map_ast_functions(bson_ast_module, function_copy_map=function_copy_map_bson)

    patch_setup = []
    for line in extract_section(module_resource, 'BSON Module Patch Setup').splitlines():
        if line.startswith('    '):
            line = line[4:]
        patch_setup.append(line)
    patch_setup = '\n'.join(patch_setup)
    patch_setup_ast = ast.parse(patch_setup)
    bson_ast_module.body.extend(patch_setup_ast.body)

    # recompile module
    source_file = bson.__file__.replace('.pyc', '.py')
    exec(compile(bson_ast_module, source_file, 'exec'), vars(bson))

if False:
# --------------------------------------------------
# |||:sec:||| PyMongo Message Module Patch Setup
# --------------------------------------------------
    if _use_c:
        bson._context._register_encoding_alternative('_insert_message', _py_insert, _cmessage._insert_message)
        bson._context.setDefault('_insert_message', _cmessage._insert_message)
    else:
        bson._context.setDefault('_insert_message', _py_insert)
    def insert(collection_name, docs, check_keys,
               safe, last_error_args, continue_on_error, uuid_subtype, context=None):
        ctx = bson._context
        return ctx._insert_message(
            collection_name, docs, check_keys,
            safe, last_error_args, continue_on_error, uuid_subtype)

    if _use_c:
        bson._context._register_encoding_alternative('_update_message', _py_update, _cmessage._update_message)
        bson._context.setDefault('_update_message', _cmessage._update_message)
    else:
        bson._context.setDefault('_update_message', _py_update)
    def update(collection_name, upsert, multi,
               spec, doc, safe, last_error_args, check_keys, uuid_subtype, context=None):
        ctx = bson._context
        return ctx._update_message(
            collection_name, upsert, multi,
            spec, doc, safe, last_error_args, check_keys, uuid_subtype)

    if _use_c:
        bson._context._register_encoding_alternative('_query_message', _py_query, _cmessage._query_message)
        bson._context.setDefault('_query_message', _cmessage._query_message)
    else:
        bson._context.setDefault('_query_message', _py_query)
    def query(options, collection_name, num_to_skip,
              num_to_return, query, field_selector=None,
              uuid_subtype=OLD_UUID_SUBTYPE, context=None):
        ctx = bson._context
        return ctx._query_message(
            options, collection_name, num_to_skip,
            num_to_return, query, field_selector,
            uuid_subtype)

    if _use_c:
        bson._context._register_encoding_alternative('_get_more_message', _py_get_more, _cmessage._get_more_message)
        bson._context.setDefault('_get_more_message', _cmessage._get_more_message)
    else:
        bson._context.setDefault('_get_more_message', _py_get_more)
    def get_more(collection_name, num_to_return, cursor_id, context=None):
        ctx = bson._context
        return ctx._get_more_message(
            collection_name, num_to_return, cursor_id)

# --------------------------------------------------
# |||:sec:||| Patch PyMongo Message Module
# --------------------------------------------------

def patch_message(module_resource):                        # ||:fnc:||
    function_copy_map_message = {
        'get_more': '_py_get_more',
        'insert': '_py_insert',
        'query': '_py_query',
        'update': '_py_update',
        }

    # get the AST tree for module
    # use pkgutil, in case the source is in a ZIP file.
    message_resource = pkgutil.get_data('pymongo', 'message.py')
    message_ast_module = ast.parse(message_resource)

    map_ast_functions(message_ast_module, function_copy_map=function_copy_map_message)

    patch_setup = []
    for line in extract_section(module_resource, 'PyMongo Message Module Patch Setup').splitlines():
        if line.startswith('    '):
            line = line[4:]
        patch_setup.append(line)
    patch_setup = '\n'.join(patch_setup)
    patch_setup_ast = ast.parse(patch_setup)
    message_ast_module.body.extend(patch_setup_ast.body)

    # recompile module
    source_file = pymongo.message.__file__.replace('.pyc', '.py')
    exec(compile(message_ast_module, source_file, 'exec'), vars(pymongo.message))

if must_patch:
    if __name__ == '__main__':
        print('--------------------------------------------------')
        dump_bson()
        print('--------------------------------------------------')
        dump_message()

    module_resource = module_resource_from_path(__file__, __name__)
    patch_bson(module_resource)
    #bson_context.export_to_bson()
    patch_message(module_resource)

# support for wrapping :func:`_element_to_bson`
if not hasattr(bson._context, '_element_to_bson'):
    bson._context.setDefault('_element_to_bson', bson._element_to_bson)
    bson._update_thread_context()

if __name__ == '__main__':
    print('--------------------------------------------------')
    dump_bson()
    print('--------------------------------------------------')
    dump_message()
    if hasattr(bson, '_context'):
        print('--------------------------------------------------')
        print(bson._context)
    print('--------------------------------------------------')

# --------------------------------------------------
# |||:sec:||| Unit Test
# --------------------------------------------------
if __name__ == '__main__':
    #
    import unittest
    from bson.son import SON

    class TestBSONContext(unittest.TestCase):                  # ||:cls:||

        def setUp(self):                                         # |:mth:|
            pass

        def test_context_dict_access(self):                      # |:mth:|

            context = bson.get_context()
            da_use_c_encoding = context['_use_c_encoding']
            self.assertEqual(da_use_c_encoding, context._use_c_encoding)
            context['_use_c_encoding'] = not da_use_c_encoding
            self.assertEqual(not da_use_c_encoding, context._use_c_encoding)

        def test_threading(self):                                # |:mth:|
            import threading
            class Thread(threading.Thread):

                def run(self):
                    sv_context = bson.lock()
                    context = bson.get_context()
                    bson.unlock(sv_context)

            sv_can_enable_threading = bson_context._can_enable_threading

            # threading cannot be re-enabled
            bson.enable_threading(False)
            self.assertRaises(bson.errors.InvalidConfiguration, bson.enable_threading, True)

            # default lock
            # no threads can be started, if this lock is held
            bson.enable_threading(False)
            sv_context = bson.lock()
            context = bson.get_context()
            bson.unlock(sv_context)

            # global thread lock
            bson_context._can_enable_threading = True
            bson.enable_threading(True)
            sv_context = bson.lock()
            context = bson.get_context()

            thread = Thread()
            thread.daemon = True
            thread.start()
            thread.join()

            bson.unlock(sv_context)

            # restore _can_enable_threading
            bson_context._can_enable_threading = sv_can_enable_threading

        def test_enable_c(self):                                 # |:mth:|
            # Make sure that all possible combinations of C/Python encoding/decoding
            # with or without system-wide available C extension work correctly.
            for _function_category in bson._context._c_functions_:
                if not bson.has_c():
                    self.assertEqual(len(_function_category), 0)
                    continue
                for _functions in _function_category:
                    self.assertTrue(repr(_functions[1]).startswith('<function'))
                    self.assertTrue(repr(_functions[2]).startswith('<built-in function'))

            document = { 'a': 99 }

            sv_context = bson.lock()
            try:
                context = bson.get_context()

                def check_c_state(self, encoding, decoding):

                    # get active context
                    context = bson.get_context()

                    if not (encoding or decoding):
                        self.assertFalse(context.is_c_enabled())
                        self.assertFalse(context.is_c_enabled(False))
                        self.assertFalse(context.is_c_enabled(True))
                    else:
                        self.assertTrue(context.is_c_enabled())
                        self.assertTrue(context.is_c_enabled(False))

                        if encoding:
                            self.assertTrue(context.is_c_encoding_enabled())
                            self.assertTrue(repr(context._dict_to_bson).startswith('<built-in function'))
                        else:
                            self.assertFalse(context.is_c_encoding_enabled())
                            self.assertTrue(repr(context._dict_to_bson).startswith('<function'))

                        if decoding:
                            self.assertTrue(context.is_c_decoding_enabled())
                            self.assertTrue(repr(context._bson_to_dict).startswith('<built-in function'))
                            self.assertTrue(repr(context.decode_all).startswith('<built-in function'))
                        else:
                            self.assertFalse(context.is_c_decoding_enabled())
                            self.assertTrue(repr(context._bson_to_dict).startswith('<function'))
                            self.assertTrue(repr(context.decode_all).startswith('<function'))

                        if encoding and decoding:
                            self.assertTrue(context.is_c_enabled(True))
                        else:
                            self.assertFalse(context.is_c_enabled(True))

                    # coverage:
                    # - C-encode,  C-decode
                    # - C-encode,  Py-decode
                    # - Py-encode, C-decode
                    # - Py-encode, Py-decode
                    try:
                        def enc(document, context=None):
                            return bson.BSON.encode(document, context=context)
                        enc(document)
                    except TypeError:
                        def enc(document, context=None):
                            return bson.BSON.encode(document)

                    self.assertEqual(99, enc(document).decode(bson.SON)["a"])
                    self.assertEqual(
                        bson._context.decode_all(
                            enc(document)
                            + enc(document)),
                        [document, document])

                context.enable_c(False)
                self.assertFalse(context.is_c_enabled(True))
                bson.set_context(context)
                check_c_state(self, False, False)

                context.enable_c(True)
                enabled = context.is_c_enabled()
                bson.set_context(context)
                if not bson.has_c():
                    self.assertFalse(enabled)
                    check_c_state(self, False, False)
                else:
                    self.assertTrue(enabled)
                    check_c_state(self, True, True)

                    context.enable_c(False)
                    self.assertFalse(context.is_c_enabled())
                    bson.set_context(context)
                    check_c_state(self, False, False)

                    context.enable_c_encoding(True)
                    self.assertTrue(context.is_c_encoding_enabled())
                    bson.set_context(context)
                    check_c_state(self, True, False)
                    context.enable_c_encoding(False)
                    self.assertFalse(context.is_c_encoding_enabled())
                    self.assertFalse(context.is_c_enabled())

                    context.enable_c_decoding(True)
                    self.assertTrue(context.is_c_decoding_enabled())
                    bson.set_context(context)
                    check_c_state(self, False, True)
                    context.enable_c_decoding(False)
                    self.assertFalse(context.is_c_decoding_enabled())
                    self.assertFalse(context.is_c_enabled())

                    context.enable_c(True)
                    bson.set_context(context)
            finally:
                bson.unlock(sv_context)

        def test_enable_c_message(self):                         # |:mth:|

            collection_name = 'test_enable_c_message'
            docs = [SON({'a': 'b'})]
            check_keys = True
            safe = False
            last_error_args = dict()
            uuid_subtype = bson.OLD_UUID_SUBTYPE

            with_c_results = []
            without_c_results = []

            def check_test_enable_c_message(results):
                continue_on_error = True
                result = pymongo.message.insert(
                    collection_name, docs, check_keys,
                    safe, last_error_args, continue_on_error, uuid_subtype, None)[1]
                result = result[:4] + result[9:]
                results.append(result)

                upsert = True
                multi = False
                spec = { '_id': 'hello' }
                doc = docs[0]
                result = pymongo.message.update(
                    collection_name, upsert, multi,
                    spec, doc, safe, last_error_args, check_keys, uuid_subtype, None)[1]
                result = result[:4] + result[9:]
                results.append(result)

                options = 0
                num_to_skip = 2
                num_to_return = 1
                query = { '_id': 'hello' }
                result = pymongo.message.query(
                    options, collection_name, num_to_skip,
                    num_to_return, query, None,
                    uuid_subtype, None)[1]
                result = result[:4] + result[9:]
                results.append(result)

                cursor_id = 555
                result = pymongo.message.get_more(
                    collection_name, num_to_return, cursor_id, None)[1]
                result = result[:4] + result[9:]
                results.append(result)

            sv_context = bson.lock()
            try:
                context = bson.get_context()
                context.enable_c(True)
                bson.set_context(context)
                check_test_enable_c_message(with_c_results)

                context.enable_c(False)
                bson.set_context(context)
                check_test_enable_c_message(without_c_results)

                for indx, result in enumerate(with_c_results):
                    self.assertEqual(result, without_c_results[indx])
            finally:
                bson.unlock(sv_context)

        def test_explicit_context(self):                         # |:mth:|

            collection_name = 'test_explicit_context'
            docs = [SON({'a': 'b'})]
            check_keys = True
            safe = False
            last_error_args = dict()
            uuid_subtype = bson.OLD_UUID_SUBTYPE
            continue_on_error = True

            sv_context = bson.lock()
            if True:
                sv_check_context = bson.check_context
                sv_message_check_context = pymongo.message.check_context
            sv_message_insert = pymongo.message.insert
            last_context_vector_was_c = []

            def dbg_insert(*args, **kwargs):
                ctx = bson._context
                if ctx is not None:
                    #print(repr(ctx._insert_message))
                    last_context_vector_was_c.append(repr(ctx._insert_message).startswith('<built-in function'))
                else:
                    last_context_vector_was_c.append(None)
                    import traceback
                    traceback.print_stack()
                return sv_message_insert(*args, **kwargs)

            try:
                if True:
                    bson.check_context = bson.dbg_check_context_required
                    pymongo.message.check_context = bson.dbg_check_context_required
                pymongo.message.insert = dbg_insert
                context = bson.get_context()
                context.enable_c(True)
                bson.set_context(context)

                result_c = pymongo.message.insert(
                    collection_name, docs, check_keys,
                    safe, last_error_args, continue_on_error, uuid_subtype, None)[1]
                result_c = result_c[:4] + result_c[9:]
                self.assertTrue(last_context_vector_was_c[-1])

                context.enable_c(False)
                bson.set_context(context)

                result_p = pymongo.message.insert(
                    collection_name, docs, check_keys,
                    safe, last_error_args, continue_on_error, uuid_subtype, None)[1]
                result_p = result_p[:4] + result_p[9:]
                self.assertFalse(last_context_vector_was_c[-1])

                self.assertEqual(result_c, result_p)

            finally:
                pymongo.message.insert = sv_message_insert
                if True:
                    pymongo.message.check_context = sv_message_check_context
                    bson.check_context = sv_check_context
                bson.unlock(sv_context)

    unittest.main()

# :ide: COMPILE: Run with python3 --verbose
# . (progn (save-buffer) (compile (concat "python3 ./" (file-name-nondirectory (buffer-file-name)) " --verbose")))

# :ide: COMPILE: Run with --verbose
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " --verbose")))
