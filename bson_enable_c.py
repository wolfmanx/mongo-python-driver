# -*- coding: utf-8 -*-

import bson

# |:sec:| enable/disable C-extension feature

_use_c_encoding = bson._use_c
_use_c_decoding = bson._use_c

_function_alternatives = [
    [],                                 # encoding
    [],                                 # decoding
    ]

def _register_encoding_alternative(name, python, c):
    _function_alternatives[0].append((name, python, c))

def _register_decoding_alternative(name, python, c):
    _function_alternatives[1].append((name, python, c))

def _enable_function_alternatives(alternatives, on=True):
    '''Return False for Python variants, True for C variants.'''
    if on and not bson.has_c():
        return False
    indx = 2 if on else 1
    for alternative in alternatives:
        setattr(bson, alternative[0], alternative[indx])
    return (True if on else False)

def enable_c_encoding(on=True):
    '''Enable/disable C extension for encoding.'''
    global _use_c_encoding
    _use_c_encoding = _enable_function_alternatives(_function_alternatives[0], on)
    return _use_c_encoding

def enable_c_decoding(on=True):
    '''Enable/disable C extension for decoding.'''
    global _use_c_decoding
    _use_c_decoding = _enable_function_alternatives(_function_alternatives[1], on)
    return _use_c_decoding

def enable_c(on=True):
    '''Enable/disable C extension for encoding/decoding.'''
    enable_c_encoding(on)
    enable_c_decoding(on)
    return _use_c_encoding and _use_c_decoding

def is_c_enabled(both=False):
    '''Check if C extension is enabled for encoding and/or decoding.

    :param both: If False (the default), the C extension is considered
      enabled if it is enabled for any of the encoding or decoding
      functions.

      If True, the C extension is considered enabled if it is enabled
      for both the encoding and decoding functions.
    '''
    if both:
        return _use_c_encoding and _use_c_decoding
    return _use_c_encoding or _use_c_decoding

# |:sec:| bson monkey-patch

import ast
import copy
import pkgutil
import bson

DECODE_ALL = """
def decode_all(data, as_class=dict, tz_aware=True):
    # This is necessary to allow `from bson import decodeall` to work
    # independent from enable_c().
    return _decode_all(data, as_class, tz_aware)
"""

function_rename_map = {
    'decode_all': '_decode_all',
    }

function_copy_map = {
    '_dict_to_bson': '_py_dict_to_bson',
    '_bson_to_dict': '_py_bson_to_dict',
    '_decode_all': '_py_decode_all',
    }

# get the AST tree for module
# use pkgutil, in case the source is in a ZIP file.
bson_init_resource = pkgutil.get_data('bson', '__init__.py')
bson_ast_module = ast.parse(bson_init_resource)

# copy Python implementations with new name
py_funcs_mapped = list()
for node in ast.walk(bson_ast_module):
    if isinstance(node, ast.FunctionDef):
        if node.name in function_rename_map:
            node.name = function_rename_map[node.name]
        if node.name in function_copy_map:
            cnode = copy.deepcopy(node)
            cnode.name = function_copy_map[node.name]
            py_funcs_mapped.append(cnode)

# append Python implementations to module
for node in py_funcs_mapped:
    bson_ast_module.body.append(node)

# recompile module
source_file = bson.__file__.replace('.pyc', '.py')
exec(compile(bson_ast_module, source_file, 'exec'), vars(bson))

# add decode_all wrapper
if bson._use_c:
    bson._decode_all = bson._cbson.decode_all
exec(DECODE_ALL, vars(bson))

# provide public enable_c API in bson
bson.enable_c_encoding = enable_c_encoding
bson.enable_c_decoding = enable_c_decoding
bson.enable_c = enable_c
bson.is_c_enabled = is_c_enabled

# setup function alternatives
if bson._use_c:
    _register_decoding_alternative('_bson_to_dict', bson._py_bson_to_dict, bson._cbson._bson_to_dict)
    _register_decoding_alternative('_decode_all', bson._py_decode_all, bson._cbson.decode_all)
    _register_encoding_alternative('_dict_to_bson', bson._py_dict_to_bson, bson._cbson._dict_to_bson)

# |:sec:| unit test
if __name__ == '__main__':
    #
    import unittest
    class TestBSON(unittest.TestCase):
        def setUp(self):
            pass

        def test_enable_c(self):
            # Make sure that all possible combinations of C/Python encoding/decoding
            # with or without system-wide available C extension work correctly.
            for _function_category in _function_alternatives:
                if not bson.has_c():
                    self.assertEqual(len(_function_category), 0)
                    continue
                for _functions in _function_category:
                    self.assertTrue(repr(_functions[1]).startswith('<function'))
                    self.assertTrue(repr(_functions[2]).startswith('<built-in function'))

            document = { 'a': 99 }

            def check_c_state(self, encoding, decoding):

                if not (encoding or decoding):
                    self.assertFalse(bson.is_c_enabled())
                    self.assertFalse(bson.is_c_enabled(False))
                    self.assertFalse(bson.is_c_enabled(True))
                else:
                    self.assertTrue(bson.is_c_enabled())
                    self.assertTrue(bson.is_c_enabled(False))

                    if encoding:
                        self.assertTrue(_use_c_encoding)
                        self.assertTrue(repr(bson._dict_to_bson).startswith('<built-in function'))
                    else:
                        self.assertFalse(_use_c_encoding)
                        self.assertTrue(repr(bson._dict_to_bson).startswith('<function'))

                    if decoding:
                        self.assertTrue(_use_c_decoding)
                        self.assertTrue(repr(bson._bson_to_dict).startswith('<built-in function'))
                        self.assertTrue(repr(bson._decode_all).startswith('<built-in function'))
                    else:
                        self.assertFalse(_use_c_decoding)
                        self.assertTrue(repr(bson._bson_to_dict).startswith('<function'))
                        self.assertTrue(repr(bson._decode_all).startswith('<function'))

                    if encoding and decoding:
                        self.assertTrue(bson.is_c_enabled(True))
                    else:
                        self.assertFalse(bson.is_c_enabled(True))

                # coverage:
                # - C-encode,  C-decode
                # - C-encode,  Py-decode
                # - Py-encode, C-decode
                # - Py-encode, Py-decode
                self.assertEqual(99, bson.BSON.encode(document).decode(bson.SON)["a"])
                self.assertEqual(
                    bson.decode_all(
                        bson.BSON.encode(document)
                        + bson.BSON.encode(document)),
                    [document, document])

            self.assertFalse(enable_c(False))
            check_c_state(self, False, False)

            enabled = enable_c(True)
            if not bson.has_c():
                self.assertFalse(enabled)
                check_c_state(self, False, False)
            else:
                self.assertTrue(enabled)
                check_c_state(self, True, True)
                enable_c(False)

                self.assertTrue(enable_c_encoding(True))
                check_c_state(self, True, False)
                self.assertFalse(enable_c_encoding(False))

                self.assertTrue(enable_c_decoding(True))
                check_c_state(self, False, True)
                self.assertFalse(enable_c_decoding(False))

    unittest.main()

# :ide: COMPILE: Run w/o args
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " ")))
