import pytest
from bson import ObjectId
from bson.errors import InvalidId

from app.models.object_id import PyObjectId


class TestPyObjectId:
    
    def test_pyobjectid_from_objectid(self):
        obj_id = ObjectId()
        py_obj_id = PyObjectId(obj_id)
        assert py_obj_id == obj_id
    
    def test_pyobjectid_from_string(self):
        obj_id_str = str(ObjectId())
        py_obj_id = PyObjectId(obj_id_str)
        assert isinstance(py_obj_id, ObjectId)
    
    def test_pyobjectid_invalid_string(self):
        with pytest.raises((InvalidId, ValueError)):
            PyObjectId("invalid")
    
    def test_pyobjectid_invalid_type(self):
        # ObjectId.is_valid(123) returns False, but ObjectId(123) raises TypeError
        # The validate function should catch this and raise ValueError
        with pytest.raises((TypeError, ValueError)):
            PyObjectId(123)
    
    def test_pyobjectid_serialization(self):
        obj_id = ObjectId()
        py_obj_id = PyObjectId(obj_id)
        assert str(py_obj_id) == str(obj_id)
    
    def test_pyobjectid_is_valid(self):
        valid_id = str(ObjectId())
        assert ObjectId.is_valid(valid_id) is True
        assert ObjectId.is_valid("invalid") is False

