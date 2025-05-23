# -*- encoding: utf-8 -*-
"""tests.help.test_doming module

"""
import pytest

import functools
from typing import Any, Type
from collections.abc import Callable
from dataclasses import dataclass, astuple, asdict, fields, field

import json
import msgpack
import cbor2 as cbor

from hio.help import RawDom, MapDom, IceMapDom, modify, modize
from hio.help.doming import dictify, datify


def test_datify():
    """
    Test convert dict to dataclass

    dataclass, astuple, asdict, fields,
    """
    @dataclass
    class Point:
        x: float
        y: float

    @dataclass
    class Line:
        a: Point
        b: Point

    line = Line(Point(1,2), Point(3,4))
    assert asdict(line) == {'a': {'x': 1, 'y': 2}, 'b': {'x': 3, 'y': 4}}
    assert line == datify(Line, asdict(line))

    pdict = dict(x=3, y=4)
    pdata = datify(Point, pdict)
    assert isinstance(pdata, Point)

    bad = dict(a=3, y=4)
    pdata = datify(Point, bad)
    assert not isinstance(pdata, Point)

    @dataclass
    class Circle:
        radius: float

        @staticmethod
        def _datify(d):
            p = d["perimeter"]
            r = p / 2 / 3.14

            return Circle(radius=r)

    d = {'area': 50.24, 'perimeter': 25.12}
    c = datify(Circle, d)
    assert c.radius == 4

    """End Test"""


def test_dictify():
    """
    Test convert dataclass to dict
    """

    @dataclass
    class Point:
        x: float
        y: float

    @dataclass
    class Line:
        a: Point
        b: Point

    line = Line(Point(1, 2), Point(3, 4))
    assert dictify(line) == {'a': {'x': 1, 'y': 2}, 'b': {'x': 3, 'y': 4}}

    @dataclass
    class Circle:
        radius: float

        def _dictify(self):
            d = dict(
                area=self.radius**2*3.14,
                perimeter=2*self.radius*3.14
            )

            return d

    c = Circle(radius=4)
    assert dictify(c) == {'area': 50.24, 'perimeter': 25.12}


def test_icemapdom():
    """Test IceMapDom dataclass """

    @dataclass(frozen=True)
    class TestDom(IceMapDom):
        name:  str = 'test'
        value:  int = 5


    td = TestDom()
    assert isinstance(td, TestDom)
    assert isinstance(td, IceMapDom)
    assert td.name == 'test'
    assert td.value == 5

    d = td._asdict()
    assert isinstance(d, dict)
    assert d == {'name': 'test', 'value': 5}

    assert td._astuple() == ("test", 5)

    assert 'name' in td
    assert 'value' in td
    """Done Test"""


def test_mapdom():
    """Test MapDom dataclass """

    @dataclass
    class TestDom(MapDom):
        name:  str = 'test'
        value:  int = 5


    td = TestDom()
    assert isinstance(td, TestDom)
    assert isinstance(td, MapDom)
    assert td.name == 'test'
    assert td.value == 5

    d = td._asdict()
    assert isinstance(d, dict)
    assert d == {'name': 'test', 'value': 5}

    assert td._astuple() == ("test", 5)

    rtd = TestDom._fromdict(d)
    assert isinstance(rtd, MapDom)
    assert isinstance(rtd, TestDom)
    assert rtd == td

    bad = dict(name='test', val=0)  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        TestDom._fromdict(bad)

    with pytest.raises(ValueError):
        MapDom._fromdict(d)  # since fields of d don't match MapDom which does not have fields

    td.name = "rest"
    td.value = 6

    assert td["name"] == 'rest'
    assert td["value"] == 6

    td["name"] = 'best'
    assert td.name == 'best'

    td._update(name='test', value=7)
    assert td.name == 'test'
    assert td.value == 7

    assert 'name' in td
    assert 'value' in td



    """Done Test"""



def test_rawdom():
    """Test RawDom dataclass """

    @dataclass
    class TestDom(RawDom):
        name:  str = 'test'
        value:  int = 5

    td = TestDom()
    assert isinstance(td, TestDom)
    assert isinstance(td, RawDom)
    assert td.name == 'test'
    assert td.value == 5

    assert td["name"] == 'test'
    assert td["value"] == 5

    td["name"] = 'best'
    assert td.name == 'best'

    td._update(name='test')
    assert td.name == 'test'

    assert 'name' in td
    assert 'value' in td

    td = TestDom()
    assert isinstance(td, TestDom)
    assert isinstance(td, RawDom)
    assert td.name == 'test'
    assert td.value == 5

    d = td._asdict()
    assert isinstance(d, dict)
    assert d == {'name': 'test', 'value': 5}

    assert td._astuple() == ("test", 5)

    rtd = TestDom._fromdict(d)
    assert isinstance(rtd, RawDom)
    assert isinstance(rtd, TestDom)
    assert rtd == td

    bad = dict(name='test', val=0)  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        TestDom._fromdict(bad)

    with pytest.raises(ValueError):
        RawDom._fromdict(d)  # since fields of d don't match RawDom which does not have fields

    s = td._asjson()
    assert isinstance(s, bytes)
    assert s == b'{"name":"test","value":5}'
    jtd = TestDom._fromjson(s)
    assert jtd == td
    s = s.decode()
    jtd = TestDom._fromjson(s)
    assert jtd == td

    bad = b'{"name":"test","val":5}'  # field label "val" instead of "value"
    with pytest.raises(ValueError):
        TestDom._fromjson(bad)

    s = td._ascbor()
    assert s == b'\xa2dnamedtestevalue\x05'
    assert isinstance(s, bytes)
    ctd = TestDom._fromcbor(s)
    assert ctd == td

    bad = cbor.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\xa2dnamedtestcval\x00'
    with pytest.raises(ValueError):
        TestDom._fromcbor(bad)

    s = td._asmgpk()
    assert s == b'\x82\xa4name\xa4test\xa5value\x05'
    assert isinstance(s, bytes)
    mtd = TestDom._frommgpk(s)
    assert mtd == td

    bad = msgpack.dumps(dict(name='test', val=0)) # field label "val" instead of "value"
    assert bad == b'\x82\xa4name\xa4test\xa3val\x00'
    with pytest.raises(ValueError):
        TestDom._frommgpk(bad)
    """Done Test"""


def test_modify():
    """Test modify wrapper. Test different use cases
    as inline wrapper with call time injected works (standard)
    as inline wrapper with default lexical works
    as inline wrapper with call time inject works that is preserved
    as decorator with default lexical works
    as decorator with call time works paramter that is preserved

    """
    @dataclass
    class TestDom(MapDom):
        count: int = 0
        names: list = field(default_factory=list)


    def fun(we):
        n0 = we(name='top')
        n1 = we()
        n2 = we()
        n3 = we()
        return(n0, n1, n2, n3)

    # Test standard wrapper call
    def we0(name=None, *, mods=None):
        m = mods
        if "count" not in m:
            m.count = 0
        if "names" not in m:
            m.names = []

        if not name:
            name = "x" + str(m.count)
        m.count += 1
        m.names.append(name)
        return name

    # first time
    works = TestDom()
    we = modify(works)(we0)  # wrapper it
    names = fun(we)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works._asdict() == {'count': 4, 'names': ['top', 'x1', 'x2', 'x3']}

    # call again as wrapped already
    names = fun(we)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works._asdict() == {'count': 8, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7']}

    # override replace works
    vorks = TestDom()
    name = we(mods=vorks)
    assert name == 'x0'
    assert vorks._asdict() == {'count': 1, 'names': ['x0']}

    # resume back befoe override
    name = we()
    assert name == 'x8'
    assert works._asdict() == {'count': 9, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7', 'x8']}

    # default lexical works in wrapper call
    def we1(name=None, *, mods=None):
        m = mods
        if "count" not in m:
            m.count = 0
        if "names" not in m:
            m.names = []

        if not name:
            name = "x" + str(m.count)
        m.count += 1
        m.names.append(name)
        return name

    # test lexical closure in wrapper
    works = None
    we = modify(works, TestDom)(we1)
    names = fun(we)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works == None  # not visible outside closure

    # call again as wrapped already
    names = fun(we)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works == None  # not visible outside closure

    # override replace works inside
    vorks = TestDom()
    name = we(mods=vorks)
    assert name == 'x0'
    assert vorks._asdict() == {'count': 1, 'names': ['x0']}

    # do again but now without override
    name = we()
    assert name == 'x8'
    assert works == None  # not visible

    # decorated
    works = TestDom()

    @modify(works)
    def we1(name=None, *, mods=None):
        m = mods
        if "count" not in m:
            m.count = 0
        if "names" not in m:
            m.names = []

        if not name:
            name = "x" + str(m.count)
        m.count += 1
        m.names.append(name)
        return name

    # test decoration with lexical scope of works, same scope in test so can view.
    # normally would be in different scopes
    names = fun(we1)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works._asdict() == {'count': 4, 'names': ['top', 'x1', 'x2', 'x3']}

    # call again
    names = fun(we1)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works._asdict() == {'count': 8, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7']}

    # override replace works
    vorks = TestDom()
    name = we1(mods=vorks)
    assert name == 'x0'
    assert vorks._asdict() == {'count': 1, 'names': ['x0']}

    # do again but now without override
    name = we1()
    assert name == 'x8'
    assert works._asdict() == {'count': 9, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7', 'x8']}

    """Done Test"""




def test_modize():
    """Test modize wrapper. Test different use cases
    as inline wrapper with call time injected works (standard)
    as inline wrapper with default lexical works
    as inline wrapper with call time inject works that is preserved
    as decorator with default lexical works
    as decorator with call time works paramter that is preserved

    """
    def fun(we):
        n0 = we(name='top')
        n1 = we()
        n2 = we()
        n3 = we()
        return(n0, n1, n2, n3)

    # Test standard wrapper call
    def we0(name=None, *, mods=None):
        m = mods
        if "count" not in m:
            m["count"] = 0
        if "names" not in m:
            m["names"] = []

        if not name:
            name = "x" + str(m["count"])
        m['count'] += 1
        m["names"].append(name)

        return name

    # first time
    works = dict(count=0, names=[])
    we = modize(works)(we0)  # wrapper it
    names = fun(we)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works == {'count': 4, 'names': ['top', 'x1', 'x2', 'x3']}

    # call again as wrapped already
    names = fun(we)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works == {'count': 8, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7']}

    # override replace works
    vorks = {}
    name = we(mods=vorks)
    assert name == 'x0'
    assert vorks == {'count': 1, 'names': ['x0']}

    # resume back befoe override
    name = we()
    assert name == 'x8'
    assert works == {'count': 9, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7', 'x8']}

    # default lexical works in wrapper call
    def we1(name=None, *, mods=None):
        w = mods
        if "count" not in w:
            w["count"] = 0
        if "names" not in w:
            w["names"] = []

        if not name:
            name = "x" + str(w["count"])
        w['count'] += 1
        w["names"].append(name)

        return name

    # test lexical closure in wrapper
    works = None
    we = modize(works)(we1)
    names = fun(we)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works == None  # not visible outside closure

    # call again as wrapped already
    names = fun(we)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works == None  # not visible outside closure

    # override replace works inside
    vorks = {}
    name = we(mods=vorks)
    assert name == 'x0'
    assert vorks == {'count': 1, 'names': ['x0']}

    # do again but now without override
    name = we()
    assert name == 'x8'
    assert works == None  # not visible

    # decorated
    works = dict(count=0, names=[])

    @modize(works)
    def we1(name=None, *, mods=None):
        w = mods
        if "count" not in w:
            w["count"] = 0
        if "names" not in w:
            w["names"] = []

        if not name:
            name = "x" + str(w["count"])
        w['count'] += 1
        w["names"].append(name)

        return name

    # test decoration with lexical scope of works, same scope in test so can view.
    # normally would be in different scopes
    names = fun(we1)
    assert names == ('top', 'x1', 'x2', 'x3')
    assert works == {'count': 4, 'names': ['top', 'x1', 'x2', 'x3']}

    # call again
    names = fun(we1)  # call again
    assert names == ('top', 'x5', 'x6', 'x7')
    assert works == {'count': 8, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7']}

    # override replace works
    vorks = {}
    name = we1(mods=vorks)
    assert name == 'x0'
    assert vorks == {'count': 1, 'names': ['x0']}

    # do again but now without override
    name = we1()
    assert name == 'x8'
    assert works == {'count': 9, 'names': ['top', 'x1', 'x2', 'x3', 'top', 'x5', 'x6', 'x7', 'x8']}

    """Done Test"""



if __name__ == "__main__":
    test_datify()
    test_dictify()
    test_icemapdom()
    test_mapdom()
    test_rawdom()
    test_modify()
    test_modize()
