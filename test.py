import json
import pytest

from metatweet import blueprint, compare
from collections import OrderedDict as O

def test_string():
    assert blueprint({"foo": "bar"}) == O({".foo": "string"})

def test_number():
    assert blueprint({"foo": 1}) == O({".foo": "number"})
    assert blueprint({"foo": 1.1}) == O({".foo": "number"})

def test_boolean():
    assert blueprint({"foo": True}) == O({".foo": "boolean"})

def test_object():
    o = {"foo": {"bar": "baz"}}
    assert blueprint(o) == O({".foo": "object", ".foo.bar": "string"})

def test_array():
    o = {"foo": [1,2,3]}
    assert blueprint(o) == O({".foo": "array", ".foo[]": "number"})

def test_array_of_objects():
    o = {"foo": [{"bar": "baz"}]}
    assert blueprint(o) == O({
        ".foo": "array", 
        ".foo[]": "object",
        ".foo[].bar": "string"
    })

def test_compare_equal():
    bp = blueprint({"foo": "bar"})
    assert compare(bp, blueprint({"foo": "bar"})) is None
    assert compare(bp, blueprint({"foo": "baz"})) is None

def test_compare_add_and_remove():
    bp1 = blueprint({"foo": "bar"})
    bp2 = blueprint({"bar": 1})

    diff = compare(bp1, bp2)
    assert diff["added"] ==  [[".bar", "number"]]
    assert diff["removed"] == [[".foo", "string"]]
    assert diff["changed"] == []

def test_null():
    bp1 = blueprint({"foo": None})
    assert bp1 == {}
