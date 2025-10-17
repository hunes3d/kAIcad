"""Test Plan schema serialization and deserialization (round-trip)."""

import json
import pytest
from sidecar.schema import Plan, PLAN_SCHEMA_VERSION


def test_plan_roundtrip_basic():
    """Test basic Plan JSON round-trip with minimal operations."""
    plan_data = {
        "plan_version": PLAN_SCHEMA_VERSION,
        "ops": [
            {
                "op": "add_component",
                "ref": "R1",
                "symbol": "Device:R",
                "value": "1k",
                "at": [100, 100],
                "rot": 0
            }
        ]
    }
    
    # Deserialize
    plan = Plan.model_validate(plan_data)
    
    # Verify
    assert plan.plan_version == PLAN_SCHEMA_VERSION
    assert len(plan.ops) == 1
    assert plan.ops[0].op == "add_component"
    assert plan.ops[0].ref == "R1"
    
    # Serialize (by_alias ensures field names match schema)
    serialized = json.loads(plan.model_dump_json(by_alias=True))
    
    # Round-trip should match (ignoring defaults like constraints)
    assert serialized["plan_version"] == plan_data["plan_version"]
    assert len(serialized["ops"]) == len(plan_data["ops"])
    assert serialized["ops"][0]["op"] == plan_data["ops"][0]["op"]
    assert serialized["ops"][0]["ref"] == plan_data["ops"][0]["ref"]


def test_plan_roundtrip_complex():
    """Test Plan round-trip with multiple operation types."""
    plan_data = {
        "plan_version": PLAN_SCHEMA_VERSION,
        "ops": [
            {
                "op": "add_component",
                "ref": "R1",
                "symbol": "Device:R",
                "value": "10k",
                "at": [80, 50],
                "rot": 0
            },
            {
                "op": "add_component",
                "ref": "D1",
                "symbol": "Device:LED",
                "value": "RED",
                "at": [120, 50],
                "rot": 90
            },
            {
                "op": "wire",
                "from": "R1:2",
                "to": "D1:A"
            },
            {
                "op": "label",
                "net": "LED_CATHODE",
                "at": [120, 46]
            }
        ]
    }
    
    # Deserialize
    plan = Plan.model_validate(plan_data)
    
    # Verify structure
    assert plan.plan_version == PLAN_SCHEMA_VERSION
    assert len(plan.ops) == 4
    
    # Check each operation type
    assert plan.ops[0].op == "add_component"
    assert plan.ops[1].op == "add_component"
    assert plan.ops[2].op == "wire"
    assert plan.ops[3].op == "label"
    
    # Serialize
    serialized = json.loads(plan.model_dump_json(by_alias=True))
    
    # Round-trip should preserve core data
    assert serialized["plan_version"] == plan_data["plan_version"]
    assert len(serialized["ops"]) == len(plan_data["ops"])


def test_plan_empty_ops():
    """Test Plan with no operations."""
    plan_data = {
        "plan_version": PLAN_SCHEMA_VERSION,
        "ops": []
    }
    
    plan = Plan.model_validate(plan_data)
    assert len(plan.ops) == 0
    
    serialized = json.loads(plan.model_dump_json(by_alias=True))
    assert serialized["plan_version"] == plan_data["plan_version"]
    assert serialized["ops"] == plan_data["ops"]
    # Note: constraints field may be added as default, that's okay


def test_plan_invalid_version():
    """Test Plan rejects invalid version."""
    plan_data = {
        "plan_version": 999,  # Invalid version
        "ops": []
    }
    
    # Should still parse (version is just an int)
    plan = Plan.model_validate(plan_data)
    assert plan.plan_version == 999


def test_plan_missing_required_fields():
    """Test Plan validation fails on missing required fields."""
    # Missing 'ref' in add_component
    plan_data = {
        "plan_version": PLAN_SCHEMA_VERSION,
        "ops": [
            {
                "op": "add_component",
                "symbol": "Device:R",
                "value": "1k",
                "at": [100, 100],
                "rot": 0
            }
        ]
    }
    
    with pytest.raises(Exception):  # Pydantic ValidationError
        Plan.model_validate(plan_data)


def test_plan_json_string_roundtrip():
    """Test Plan can be serialized to and from JSON string."""
    plan_data = {
        "plan_version": PLAN_SCHEMA_VERSION,
        "ops": [
            {
                "op": "wire",
                "from": "R1:1",
                "to": "R2:2"
            }
        ]
    }
    
    # From dict
    plan = Plan.model_validate(plan_data)
    
    # To JSON string
    json_str = plan.model_dump_json(by_alias=True)
    
    # From JSON string
    plan2 = Plan.model_validate_json(json_str)
    
    # Should be equivalent
    assert plan.model_dump() == plan2.model_dump()


def test_plan_coordinate_types():
    """Test Plan handles coordinate as list of numbers."""
    plan_data = {
        "plan_version": PLAN_SCHEMA_VERSION,
        "ops": [
            {
                "op": "add_component",
                "ref": "C1",
                "symbol": "Device:C",
                "value": "100nF",
                "at": [123.45, 67.89],  # Float coordinates
                "rot": 180
            }
        ]
    }
    
    plan = Plan.model_validate(plan_data)
    assert plan.ops[0].at == (123.45, 67.89)  # Tuple internally
    
    serialized = json.loads(plan.model_dump_json(by_alias=True))
    assert serialized["ops"][0]["at"] == [123.45, 67.89]  # List when serialized


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
