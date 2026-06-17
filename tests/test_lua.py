import re
import __main__

import pytest


class MyClass:
    def __repr__(self):
        return '<MyClass>'


obj = MyClass()
__main__.obj = obj


def _assert_repr(value, pattern):
    assert re.fullmatch(pattern, repr(value))


@pytest.fixture(scope='module')
def lua():
    return pytest.importorskip('lua')


def test_globals_reference(lua):
    lg = lua.globals()
    assert lg == lg._G
    assert lg._G == lg._G
    assert lg._G == lg['_G']


def test_assign_python_values(lua):
    lg = lua.globals()

    lg.foo = 'bar'
    assert lg.foo == 'bar'

    lg.tmp = []
    assert lg.tmp == []


def test_lua_table_access(lua):
    lg = lua.globals()

    lua.execute('x = {1, 2, 3, foo = {4, 5}}')
    assert (lg.x[1], lg.x[2], lg.x[3]) == (1, 2, 3)
    assert (lg.x['foo'][1], lg.x['foo'][2]) == (4, 5)


def test_lua_module_and_string(lua):
    lg = lua.globals()

    assert lua.require.__name__ == 'require'

    _assert_repr(lg.string, r'<Lua table at 0x[0-9a-fA-F]+>')
    _assert_repr(lg.string.lower, r'<Lua function at 0x[0-9a-fA-F]+>')
    assert lg.string.lower('Hello world!') == 'hello world!'


def test_python_dict_round_trip(lua):
    lg = lua.globals()

    d = {}
    lg.d = d
    lua.execute("d['key'] = 'value'")
    assert d['key'] == 'value'

    d2 = lua.eval('d')
    assert d is d2


def test_python_interface_access(lua):
    __main__.lua = lua
    lua.execute("python = require 'python'")

    _assert_repr(lua.eval('python'), r'<Lua table at 0x[0-9a-fA-F]+>')
    assert lua.eval("python.eval 'obj'") is obj
    assert lua.eval("""python.eval([[lua.eval('python.eval(\"obj\")')]])""") is obj

    lua.execute('pg = python.globals()')
    assert lua.eval('pg.obj') is obj


def test_asfunc_and_table_iteration(lua):
    observed = []

    def show(key, value):
        observed.append((key, value))

    asfunc = lua.eval('python.asfunc')
    _assert_repr(asfunc, r'<Lua function at 0x[0-9a-fA-F]+>')

    l = ['a', 'b', 'c']
    t = lua.eval('{a=1, b=2, c=3}')

    for k in l:
        show(k, t[k])

    assert observed == [('a', 1), ('b', 2), ('c', 3)]
