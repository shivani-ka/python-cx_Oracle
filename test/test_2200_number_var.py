#------------------------------------------------------------------------------
# Copyright (c) 2016, 2020, Oracle and/or its affiliates. All rights reserved.
#
# Portions Copyright 2007-2015, Anthony Tuininga. All rights reserved.
#
# Portions Copyright 2001-2007, Computronix (Canada) Ltd., Edmonton, Alberta,
# Canada. All rights reserved.
#------------------------------------------------------------------------------

"""
2200 - Module for testing number variables
"""

import TestEnv

import cx_Oracle
import decimal
import sys

class TestCase(TestEnv.BaseTestCase):

    def outputTypeHandlerNativeInt(self, cursor, name, defaultType, size,
            precision, scale):
        return cursor.var(cx_Oracle.DB_TYPE_BINARY_INTEGER,
                arraysize=cursor.arraysize)

    def outputTypeHandlerDecimal(self, cursor, name, defaultType, size,
            precision, scale):
        if defaultType == cx_Oracle.NUMBER:
            return cursor.var(str, 255, outconverter = decimal.Decimal,
                    arraysize = cursor.arraysize)

    def setUp(self):
        TestEnv.BaseTestCase.setUp(self)
        self.rawData = []
        self.dataByKey = {}
        for i in range(1, 11):
            numberCol = i + i * 0.25
            floatCol = i + i * 0.75
            unconstrainedCol = i ** 3 + i * 0.5
            if i % 2:
                nullableCol = 143 ** i
            else:
                nullableCol = None
            dataTuple = (i, 38 ** i, numberCol, floatCol,
                    unconstrainedCol, nullableCol)
            self.rawData.append(dataTuple)
            self.dataByKey[i] = dataTuple

    def test_2200_BindBoolean(self):
        "2200 - test binding in a boolean"
        result = self.cursor.callfunc("pkg_TestBooleans.GetStringRep", str,
                (True,))
        self.assertEqual(result, "TRUE")

    def test_2201_BindBooleanAsNumber(self):
        "2201 - test binding in a boolean as a number"
        var = self.cursor.var(cx_Oracle.NUMBER)
        var.setvalue(0, True)
        self.cursor.execute("select :1 from dual", [var])
        result, = self.cursor.fetchone()
        self.assertEqual(result, 1)
        var.setvalue(0, False)
        self.cursor.execute("select :1 from dual", [var])
        result, = self.cursor.fetchone()
        self.assertEqual(result, 0)

    def test_2202_BindDecimal(self):
        "2202 - test binding in a decimal.Decimal"
        self.cursor.execute("""
                select * from TestNumbers
                where NumberCol - :value1 - :value2 = trunc(NumberCol)""",
                value1 = decimal.Decimal("0.20"),
                value2 = decimal.Decimal("0.05"))
        self.assertEqual(self.cursor.fetchall(),
                [self.dataByKey[1], self.dataByKey[5], self.dataByKey[9]])

    def test_2203_BindFloat(self):
        "2203 - test binding in a float"
        self.cursor.execute("""
                select * from TestNumbers
                where NumberCol - :value = trunc(NumberCol)""",
                value = 0.25)
        self.assertEqual(self.cursor.fetchall(),
                [self.dataByKey[1], self.dataByKey[5], self.dataByKey[9]])

    def test_2204_BindInteger(self):
        "2204 - test binding in an integer"
        self.cursor.execute("""
                select * from TestNumbers
                where IntCol = :value""",
                value = 2)
        self.assertEqual(self.cursor.fetchall(), [self.dataByKey[2]])

    def test_2205_BindLargeLongAsOracleNumber(self):
        "2205 - test binding in a large long integer as Oracle number"
        valueVar = self.cursor.var(cx_Oracle.NUMBER)
        valueVar.setvalue(0, 6088343244)
        self.cursor.execute("""
                begin
                  :value := :value + 5;
                end;""",
                value = valueVar)
        value = valueVar.getvalue()
        self.assertEqual(value, 6088343249)

    def test_2206_BindLargeLongAsInteger(self):
        "2206 - test binding in a large long integer as Python integer"
        longValue = -9999999999999999999
        self.cursor.execute("select :value from dual", value = longValue)
        result, = self.cursor.fetchone()
        self.assertEqual(result, longValue)

    def test_2207_BindIntegerAfterString(self):
        "2207 - test binding in an integer after setting input sizes to string"
        self.cursor.setinputsizes(value = 15)
        self.cursor.execute("""
                select * from TestNumbers
                where IntCol = :value""",
                value = 3)
        self.assertEqual(self.cursor.fetchall(), [self.dataByKey[3]])

    def test_2208_BindDecimalAfterNumber(self):
        "2208 - test binding in a decimal after setting input sizes to number"
        cursor = self.connection.cursor()
        value = decimal.Decimal("319438950232418390.273596")
        cursor.setinputsizes(value = cx_Oracle.NUMBER)
        cursor.outputtypehandler = self.outputTypeHandlerDecimal
        cursor.execute("select :value from dual",
                value = value)
        outValue, = cursor.fetchone()
        self.assertEqual(outValue, value)

    def test_2209_BindNull(self):
        "2209 - test binding in a null"
        self.cursor.execute("""
                select * from TestNumbers
                where IntCol = :value""",
                value = None)
        self.assertEqual(self.cursor.fetchall(), [])

    def test_2210_BindNumberArrayDirect(self):
        "2210 - test binding in a number array"
        returnValue = self.cursor.var(cx_Oracle.NUMBER)
        array = [r[2] for r in self.rawData]
        statement = """
                begin
                  :returnValue := pkg_TestNumberArrays.TestInArrays(
                      :startValue, :array);
                end;"""
        self.cursor.execute(statement,
                returnValue = returnValue,
                startValue = 5,
                array = array)
        self.assertEqual(returnValue.getvalue(), 73.75)
        array = list(range(15))
        self.cursor.execute(statement,
                startValue = 10,
                array = array)
        self.assertEqual(returnValue.getvalue(), 115.0)

    def test_2211_BindNumberArrayBySizes(self):
        "2211 - test binding in a number array (with setinputsizes)"
        returnValue = self.cursor.var(cx_Oracle.NUMBER)
        self.cursor.setinputsizes(array = [cx_Oracle.NUMBER, 10])
        array = [r[2] for r in self.rawData]
        self.cursor.execute("""
                begin
                  :returnValue := pkg_TestNumberArrays.TestInArrays(
                      :startValue, :array);
                end;""",
                returnValue = returnValue,
                startValue = 6,
                array = array)
        self.assertEqual(returnValue.getvalue(), 74.75)

    def test_2212_BindNumberArrayByVar(self):
        "2212 - test binding in a number array (with arrayvar)"
        returnValue = self.cursor.var(cx_Oracle.NUMBER)
        array = self.cursor.arrayvar(cx_Oracle.NUMBER,
                [r[2] for r in self.rawData])
        self.cursor.execute("""
                begin
                  :returnValue := pkg_TestNumberArrays.TestInArrays(
                      :integerValue, :array);
                end;""",
                returnValue = returnValue,
                integerValue = 7,
                array = array)
        self.assertEqual(returnValue.getvalue(), 75.75)

    def test_2213_BindZeroLengthNumberArrayByVar(self):
        "2213 - test binding in a zero length number array (with arrayvar)"
        returnValue = self.cursor.var(cx_Oracle.NUMBER)
        array = self.cursor.arrayvar(cx_Oracle.NUMBER, 0)
        self.cursor.execute("""
                begin
                  :returnValue := pkg_TestNumberArrays.TestInArrays(
                      :integerValue, :array);
                end;""",
                returnValue = returnValue,
                integerValue = 8,
                array = array)
        self.assertEqual(returnValue.getvalue(), 8.0)
        self.assertEqual(array.getvalue(), [])

    def test_2214_BindInOutNumberArrayByVar(self):
        "2214 - test binding in/out a number array (with arrayvar)"
        array = self.cursor.arrayvar(cx_Oracle.NUMBER, 10)
        originalData = [r[2] for r in self.rawData]
        expectedData = [originalData[i - 1] * 10 for i in range(1, 6)] + \
                originalData[5:]
        array.setvalue(0, originalData)
        self.cursor.execute("""
                begin
                  pkg_TestNumberArrays.TestInOutArrays(:numElems, :array);
                end;""",
                numElems = 5,
                array = array)
        self.assertEqual(array.getvalue(), expectedData)

    def test_2215_BindOutNumberArrayByVar(self):
        "2215 - test binding out a Number array (with arrayvar)"
        array = self.cursor.arrayvar(cx_Oracle.NUMBER, 6)
        expectedData = [i * 100 for i in range(1, 7)]
        self.cursor.execute("""
                begin
                  pkg_TestNumberArrays.TestOutArrays(:numElems, :array);
                end;""",
                numElems = 6,
                array = array)
        self.assertEqual(array.getvalue(), expectedData)

    def test_2216_BindOutSetInputSizes(self):
        "2216 - test binding out with set input sizes defined"
        vars = self.cursor.setinputsizes(value = cx_Oracle.NUMBER)
        self.cursor.execute("""
                begin
                  :value := 5;
                end;""")
        self.assertEqual(vars["value"].getvalue(), 5)

    def test_2217_BindInOutSetInputSizes(self):
        "2217 - test binding in/out with set input sizes defined"
        vars = self.cursor.setinputsizes(value = cx_Oracle.NUMBER)
        self.cursor.execute("""
                begin
                  :value := :value + 5;
                end;""",
                value = 1.25)
        self.assertEqual(vars["value"].getvalue(), 6.25)

    def test_2218_BindOutVar(self):
        "2218 - test binding out with cursor.var() method"
        var = self.cursor.var(cx_Oracle.NUMBER)
        self.cursor.execute("""
                begin
                  :value := 5;
                end;""",
                value = var)
        self.assertEqual(var.getvalue(), 5)

    def test_2219_BindInOutVarDirectSet(self):
        "2219 - test binding in/out with cursor.var() method"
        var = self.cursor.var(cx_Oracle.NUMBER)
        var.setvalue(0, 2.25)
        self.cursor.execute("""
                begin
                  :value := :value + 5;
                end;""",
                value = var)
        self.assertEqual(var.getvalue(), 7.25)

    def test_2220_CursorDescription(self):
        "2220 - test cursor description is accurate"
        self.cursor.execute("select * from TestNumbers")
        self.assertEqual(self.cursor.description,
                [ ('INTCOL', cx_Oracle.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
                  ('LONGINTCOL', cx_Oracle.DB_TYPE_NUMBER, 17, None, 16, 0, 0),
                  ('NUMBERCOL', cx_Oracle.DB_TYPE_NUMBER, 13, None, 9, 2, 0),
                  ('FLOATCOL', cx_Oracle.DB_TYPE_NUMBER, 127, None, 126, -127,
                        0),
                  ('UNCONSTRAINEDCOL', cx_Oracle.DB_TYPE_NUMBER, 127, None, 0,
                        -127, 0),
                  ('NULLABLECOL', cx_Oracle.DB_TYPE_NUMBER, 39, None, 38, 0,
                        1) ])

    def test_2221_FetchAll(self):
        "2221 - test that fetching all of the data returns the correct results"
        self.cursor.execute("select * From TestNumbers order by IntCol")
        self.assertEqual(self.cursor.fetchall(), self.rawData)
        self.assertEqual(self.cursor.fetchall(), [])

    def test_2222_FetchMany(self):
        "2222 - test that fetching data in chunks returns the correct results"
        self.cursor.execute("select * From TestNumbers order by IntCol")
        self.assertEqual(self.cursor.fetchmany(3), self.rawData[0:3])
        self.assertEqual(self.cursor.fetchmany(2), self.rawData[3:5])
        self.assertEqual(self.cursor.fetchmany(4), self.rawData[5:9])
        self.assertEqual(self.cursor.fetchmany(3), self.rawData[9:])
        self.assertEqual(self.cursor.fetchmany(3), [])

    def test_2223_FetchOne(self):
        "2223 - test that fetching a single row returns the correct results"
        self.cursor.execute("""
                select *
                from TestNumbers
                where IntCol in (3, 4)
                order by IntCol""")
        self.assertEqual(self.cursor.fetchone(), self.dataByKey[3])
        self.assertEqual(self.cursor.fetchone(), self.dataByKey[4])
        self.assertEqual(self.cursor.fetchone(), None)

    def test_2224_ReturnAsLong(self):
        "2224 - test that fetching a long integer returns such in Python"
        self.cursor.execute("""
                select NullableCol
                from TestNumbers
                where IntCol = 9""")
        col, = self.cursor.fetchone()
        self.assertEqual(col, 25004854810776297743)

    def test_2225_ReturnConstantFloat(self):
        "2225 - test fetching a floating point number returns such in Python"
        self.cursor.execute("select 1.25 from dual")
        result, = self.cursor.fetchone()
        self.assertEqual(result, 1.25)

    def test_2226_ReturnConstantInteger(self):
        "2226 - test that fetching an integer returns such in Python"
        self.cursor.execute("select 148 from dual")
        result, = self.cursor.fetchone()
        self.assertEqual(result, 148)
        self.assertTrue(isinstance(result, int), "integer not returned")

    def test_2227_AcceptableBoundaryNumbers(self):
        "2227 - test that acceptable boundary numbers are handled properly"
        inValues = [decimal.Decimal("9.99999999999999e+125"),
                decimal.Decimal("-9.99999999999999e+125"), 0.0, 1e-130,
                -1e-130]
        outValues = [int("9" * 15 + "0" * 111), -int("9" * 15 + "0" * 111),
                0, 1e-130, -1e-130]
        for inValue, outValue in zip(inValues, outValues):
            self.cursor.execute("select :1 from dual", (inValue,))
            result, = self.cursor.fetchone()
            self.assertEqual(result, outValue)

    def test_2228_UnacceptableBoundaryNumbers(self):
        "2228 - test that unacceptable boundary numbers are rejected"
        inValues = [1e126, -1e126, float("inf"), float("-inf"),
                float("NaN"), decimal.Decimal("1e126"),
                decimal.Decimal("-1e126"), decimal.Decimal("inf"),
                decimal.Decimal("-inf"), decimal.Decimal("NaN")]
        noRepErr = "DPI-1044: value cannot be represented as an Oracle number"
        invalidErr = ""
        expectedErrors = [noRepErr, noRepErr, invalidErr, invalidErr,
                invalidErr, noRepErr, noRepErr, invalidErr, invalidErr,
                invalidErr]
        for inValue, error in zip(inValues, expectedErrors):
            method = self.assertRaisesRegex if sys.version_info[0] == 3 \
                    else self.assertRaisesRegexp
            method(cx_Oracle.DatabaseError, error, self.cursor.execute,
                    "select :1 from dual", (inValue,))

    def test_2229_ReturnFloatFromDivision(self):
        "2229 - test that fetching the result of division returns a float"
        self.cursor.execute("""
                select IntCol / 7
                from TestNumbers
                where IntCol = 1""")
        result, = self.cursor.fetchone()
        self.assertEqual(result, 1.0 / 7.0)
        self.assertTrue(isinstance(result, float), "float not returned")

    def test_2230_StringFormat(self):
        "2230 - test that string format is returned properly"
        var = self.cursor.var(cx_Oracle.NUMBER)
        self.assertEqual(str(var),
                "<cx_Oracle.Var of type DB_TYPE_NUMBER with value None>")
        var.setvalue(0, 4)
        self.assertEqual(str(var),
                "<cx_Oracle.Var of type DB_TYPE_NUMBER with value 4.0>")

    def test_2231_BindNativeFloat(self):
        "2231 - test that binding native float is possible"
        self.cursor.setinputsizes(cx_Oracle.DB_TYPE_BINARY_DOUBLE)
        self.cursor.execute("select :1 from dual", (5,))
        self.assertEqual(self.cursor.bindvars[0].type,
                cx_Oracle.DB_TYPE_BINARY_DOUBLE)
        value, = self.cursor.fetchone()
        self.assertEqual(value, 5)
        self.cursor.execute("select :1 from dual", (1.5,))
        self.assertEqual(self.cursor.bindvars[0].type,
                cx_Oracle.DB_TYPE_BINARY_DOUBLE)
        value, = self.cursor.fetchone()
        self.assertEqual(value, 1.5)
        self.cursor.execute("select :1 from dual", (decimal.Decimal("NaN"),))
        self.assertEqual(self.cursor.bindvars[0].type,
                cx_Oracle.DB_TYPE_BINARY_DOUBLE)
        value, = self.cursor.fetchone()
        self.assertEqual(str(value), str(float("NaN")))

    def test_2232_FetchNativeInt(self):
        "2232 - test fetching numbers as native integers"
        self.cursor.outputtypehandler = self.outputTypeHandlerNativeInt
        for value in (1, 2 ** 31, 2 ** 63 - 1, -1, -2 ** 31, -2 ** 63 + 1):
            self.cursor.execute("select :1 from dual", [str(value)])
            fetchedValue, = self.cursor.fetchone()
            self.assertEqual(value, fetchedValue)

if __name__ == "__main__":
    TestEnv.RunTestCases()