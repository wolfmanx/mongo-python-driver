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

"""Test the bson module context."""

import sysconfig
import sys
import os

sys.path[0:0] = [""]

if __name__ == '__main__':
    # put build directory at beginning of path
    build_lib_dir = os.path.join(os.path.pardir)
    if os.path.exists(os.path.join(build_lib_dir, 'test')) and build_lib_dir not in sys.path:
        sys.path.insert(0, build_lib_dir)
    build_lib_dir = ''.join(('build/lib.', sysconfig.get_platform(), '-', str(sys.version_info[0]), '.', str(sys.version_info[1])))
    if os.path.exists(build_lib_dir) and build_lib_dir not in sys.path:
        sys.path.insert(0, build_lib_dir)
    build_lib_dir = os.path.join(os.path.pardir, build_lib_dir)
    if os.path.exists(build_lib_dir) and build_lib_dir not in sys.path:
        sys.path.insert(0, build_lib_dir)

import unittest
import datetime
import re

from nose.plugins.skip import SkipTest

import bson
import bson.errors
from bson.son import SON
import pymongo.message

PY3 = sys.version_info[0] == 3

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

        sv_can_enable_threading = bson.context._can_enable_threading

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
        bson.context._can_enable_threading = True
        bson.enable_threading(True)
        sv_context = bson.lock()
        context = bson.get_context()

        thread = Thread()
        thread.daemon = True
        thread.start()
        thread.join()

        bson.unlock(sv_context)

        # restore _can_enable_threading
        bson.context._can_enable_threading = sv_can_enable_threading

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

    def test_enable_c_message(self):                                 # |:mth:|

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
                    safe, last_error_args, continue_on_error, uuid_subtype)[1]
            result = result[:4] + result[9:]
            results.append(result)

            upsert = True
            multi = False
            spec = { '_id': 'hello' }
            doc = docs[0]
            result = pymongo.message.update(
                collection_name, upsert, multi,
                spec, doc, safe, last_error_args, check_keys, uuid_subtype)[1]
            result = result[:4] + result[9:]
            results.append(result)

            options = 0
            num_to_skip = 2
            num_to_return = 1
            query = { '_id': 'hello' }
            result = pymongo.message.query(
                options, collection_name, num_to_skip,
                num_to_return, query, None,
                uuid_subtype)[1]
            result = result[:4] + result[9:]
            results.append(result)

            cursor_id = 555
            result = pymongo.message.get_more(
                collection_name, num_to_return, cursor_id)[1]
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

if __name__ == "__main__":
    unittest.main()

# :ide: COMPILE: Run with python3
# . (progn (save-buffer) (compile (concat "python3 ./" (file-name-nondirectory (buffer-file-name)) " ")))

# :ide: COMPILE: Run w/o args
# . (progn (save-buffer) (compile (concat "python ./" (file-name-nondirectory (buffer-file-name)) " ")))

# :ide: +-#+
# . Compile ()
