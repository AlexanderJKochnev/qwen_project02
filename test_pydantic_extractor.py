from pydantic_key_extractor import extract_keys_with_blacklist
from pydantic import BaseModel
from typing import List, Optional
import json


def test_basic_extraction():
    """Test basic functionality"""
    class Address(BaseModel):
        street: str
        city: str
        country: str

    class User(BaseModel):
        name: str
        email: str
        age: int
        address: Address

    blacklist = ['email']
    result = extract_keys_with_blacklist(User, blacklist)
    expected = ['name', 'age', 'address', 'address.street', 'address.city', 'address.country']
    assert sorted(result) == sorted(expected), f"Expected {expected}, got {result}"
    print("✓ Basic extraction test passed")


def test_nested_blacklist():
    """Test excluding nested fields"""
    class Address(BaseModel):
        street: str
        city: str
        country: str

    class User(BaseModel):
        name: str
        email: str
        address: Address

    blacklist = ['country']  # Exclude nested field
    result = extract_keys_with_blacklist(User, blacklist)
    expected = ['name', 'email', 'address', 'address.street', 'address.city']
    assert sorted(result) == sorted(expected), f"Expected {expected}, got {result}"
    print("✓ Nested blacklist test passed")


def test_list_extraction():
    """Test extraction with lists"""
    class PhoneNumber(BaseModel):
        number: str
        type: str

    class User(BaseModel):
        name: str
        emails: List[str]
        phones: List[PhoneNumber]

    blacklist = ['type']
    result = extract_keys_with_blacklist(User, blacklist)
    expected = ['name', 'emails', 'phones', 'phones[].number']
    assert sorted(result) == sorted(expected), f"Expected {expected}, got {result}"
    print("✓ List extraction test passed")


def test_multiple_levels_of_nesting():
    """Test multiple levels of nesting"""
    class Country(BaseModel):
        name: str
        code: str
        continent: str

    class Address(BaseModel):
        street: str
        city: str
        country: Country

    class User(BaseModel):
        name: str
        email: str
        addresses: List[Address]

    blacklist = ['email', 'continent']
    result = extract_keys_with_blacklist(User, blacklist)
    expected = [
        'name',
        'addresses',
        'addresses[].street',
        'addresses[].city',
        'addresses[].country',
        'addresses[].country.name',
        'addresses[].country.code'
    ]
    assert sorted(result) == sorted(expected), f"Expected {expected}, got {result}"
    print("✓ Multiple levels of nesting test passed")


def test_empty_blacklist():
    """Test with empty blacklist"""
    class Address(BaseModel):
        street: str
        city: str

    class User(BaseModel):
        name: str
        address: Address

    blacklist = []
    result = extract_keys_with_blacklist(User, blacklist)
    expected = ['name', 'address', 'address.street', 'address.city']
    assert sorted(result) == sorted(expected), f"Expected {expected}, got {result}"
    print("✓ Empty blacklist test passed")


def test_all_blacklisted():
    """Test when all fields are blacklisted"""
    class User(BaseModel):
        name: str
        email: str

    blacklist = ['name', 'email']
    result = extract_keys_with_blacklist(User, blacklist)
    expected = []
    assert sorted(result) == sorted(expected), f"Expected {expected}, got {result}"
    print("✓ All blacklisted test passed")


def test_circular_reference():
    """Test handling circular references"""
    class Node(BaseModel):
        value: str
        children: List['Node']

    blacklist = ['value']
    result = extract_keys_with_blacklist(Node, blacklist)
    expected = ['children']
    assert sorted(result) == sorted(expected), f"Expected {expected}, got {result}"
    print("✓ Circular reference test passed")


if __name__ == "__main__":
    print("Running tests...")
    test_basic_extraction()
    test_nested_blacklist()
    test_list_extraction()
    test_multiple_levels_of_nesting()
    test_empty_blacklist()
    test_all_blacklisted()
    test_circular_reference()
    print("\nAll tests passed! ✓")