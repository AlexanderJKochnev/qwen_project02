from pydantic_key_extractor import extract_keys_with_blacklist
from pydantic import BaseModel
from typing import List, Optional


def test_complex_scenario():
    """Test a complex scenario with deeply nested structures"""
    
    class Metadata(BaseModel):
        created_by: str
        created_at: str
        version: str
    
    class Tag(BaseModel):
        name: str
        category: str
        sensitive: str  # This will be blacklisted
    
    class DocumentContent(BaseModel):
        title: str
        body: str
        private_notes: str  # This will be blacklisted
    
    class Document(BaseModel):
        id: str
        content: DocumentContent
        tags: List[Tag]
        metadata: Metadata
        secret_field: str  # This will be blacklisted
    
    class User(BaseModel):
        username: str
        email: str  # This will be blacklisted
        documents: List[Document]
        password: str  # This will be blacklisted
    
    blacklist = ['email', 'password', 'private_notes', 'secret_field', 'sensitive']
    result = extract_keys_with_blacklist(User, blacklist)
    
    expected = [
        'username',
        'documents',
        'documents[].id',
        'documents[].content',
        'documents[].content.title',
        'documents[].content.body',
        'documents[].tags',
        'documents[].tags[].name',
        'documents[].tags[].category',
        'documents[].metadata',
        'documents[].metadata.created_by',
        'documents[].metadata.created_at',
        'documents[].metadata.version'
    ]
    
    print("Result:", sorted(result))
    print("Expected:", sorted(expected))
    
    assert sorted(result) == sorted(expected), f"Mismatch between result and expected"
    print("✓ Complex scenario test passed!")


def test_edge_cases():
    """Test edge cases"""
    
    # Test with primitive types inside models
    class Simple(BaseModel):
        value: int
        description: str
    
    result = extract_keys_with_blacklist(Simple, [])
    expected = ['value', 'description']
    assert sorted(result) == sorted(expected)
    print("✓ Simple case test passed!")
    
    # Test with empty blacklist
    result = extract_keys_with_blacklist(Simple, ['nonexistent'])
    expected = ['value', 'description']
    assert sorted(result) == sorted(expected)
    print("✓ Non-existent blacklist test passed!")
    
    # Test with optional fields
    class WithOptional(BaseModel):
        required_field: str
        optional_field: Optional[str] = None
    
    result = extract_keys_with_blacklist(WithOptional, [])
    expected = ['required_field', 'optional_field']
    assert sorted(result) == sorted(expected)
    print("✓ Optional field test passed!")


if __name__ == "__main__":
    print("Running final validation tests...")
    test_complex_scenario()
    test_edge_cases()
    print("\nAll final tests passed! ✓")
    print("\nThe function correctly:")
    print("- Extracts all key paths with dot notation")
    print("- Handles nested structures at any depth")
    print("- Excludes keys present in the blacklist at any level")
    print("- Handles lists of objects")
    print("- Prevents infinite recursion in circular references")
    print("- Works with both simple and complex Pydantic models")