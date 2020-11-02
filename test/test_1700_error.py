#------------------------------------------------------------------------------
# Copyright (c) 2016, 2020, Oracle and/or its affiliates. All rights reserved.
#
# Portions Copyright 2007-2015, Anthony Tuininga. All rights reserved.
#
# Portions Copyright 2001-2007, Computronix (Canada) Ltd., Edmonton, Alberta,
# Canada. All rights reserved.
#------------------------------------------------------------------------------

"""
1700 - Module for testing error objects
"""

import TestEnv

import cx_Oracle
import pickle

class TestCase(TestEnv.BaseTestCase):

    def test_1700_ParseError(self):
        "1700 - test parse error returns offset correctly"
        with self.assertRaises(cx_Oracle.Error) as cm:
            self.cursor.execute("begin t_Missing := 5; end;")
        errorObj, = cm.exception.args
        self.assertEqual(errorObj.offset, 6)

    def test_1701_PickleError(self):
        "1701 - test picking/unpickling an error object"
        with self.assertRaises(cx_Oracle.Error) as cm:
            self.cursor.execute("""
                    begin
                        raise_application_error(-20101, 'Test!');
                    end;""")
        errorObj, = cm.exception.args
        self.assertEqual(type(errorObj), cx_Oracle._Error)
        self.assertTrue("Test!" in errorObj.message)
        self.assertEqual(errorObj.code, 20101)
        self.assertEqual(errorObj.offset, 0)
        self.assertTrue(isinstance(errorObj.isrecoverable, bool))
        pickledData = pickle.dumps(errorObj)
        newErrorObj = pickle.loads(pickledData)
        self.assertEqual(type(newErrorObj), cx_Oracle._Error)
        self.assertTrue(newErrorObj.message == errorObj.message)
        self.assertTrue(newErrorObj.code == errorObj.code)
        self.assertTrue(newErrorObj.offset == errorObj.offset)
        self.assertTrue(newErrorObj.context == errorObj.context)
        self.assertTrue(newErrorObj.isrecoverable == errorObj.isrecoverable)

if __name__ == "__main__":
    TestEnv.RunTestCases()