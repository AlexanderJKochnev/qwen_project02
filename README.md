# wine_project01

This repository contains a full-stack application with a Preact frontend and Python backend.

## Frontend: preact_front

The frontend is built with Preact and includes:

- Internationalization (i18n) support for English and Russian
- Language context with automatic detection and localStorage persistence
- Comprehensive translation dictionary with common UI terms
- Responsive design with Tailwind CSS and DaisyUI

### Language Context Features

- Automatic language detection based on browser language
- Persistent language preference using localStorage
- Comprehensive translation dictionary with common UI terms
- Easy-to-use translation function

To run the frontend:

```bash
cd preact_front
npm install
npm run dev
```

## Backend

The backend is built with Python and includes various components for a complete web application.

## Pydantic Key Extractor Utility

A utility function that extracts all key paths from a Pydantic schema with dot notation for full depth of nesting, excluding keys that have values in the blacklist at any level of nesting.

### Function Signature

```python
def extract_keys_with_blacklist(schema: type, blacklist: List[str]) -> List[str]:
```

### Parameters

- `schema`: Pydantic model class to extract keys from
- `blacklist`: List of keys to exclude from the result at any level of nesting

### Returns

- `List[str]`: List of key paths in dot notation representing all fields in the schema except those in the blacklist

### Features

- **Full Depth Extraction**: Extracts keys from arbitrarily nested structures
- **Dot Notation**: Uses dot notation for nested fields (e.g., `user.address.street`)
- **Blacklist Support**: Excludes specified keys at any level of nesting
- **List Handling**: Properly handles lists of objects with `[]` notation (e.g., `users[].name`)
- **Circular Reference Protection**: Safeguards against infinite recursion in self-referencing models
- **Pydantic v2 Compatible**: Works with modern Pydantic models

### Examples

```python
from pydantic_key_extractor import extract_keys_with_blacklist
from pydantic import BaseModel
from typing import List

class Address(BaseModel):
    street: str
    city: str
    country: str

class PhoneNumber(BaseModel):
    number: str
    type: str

class User(BaseModel):
    name: str
    email: str
    age: int
    address: Address
    phone_numbers: List[PhoneNumber]

# Extract all keys except 'email' and 'country'
blacklist = ['email', 'country']
keys = extract_keys_with_blacklist(User, blacklist)
# Result: ['name', 'age', 'address', 'address.street', 'address.city', 
#          'phone_numbers', 'phone_numbers[].number', 'phone_numbers[].type']
```

### Usage Notes

- The function handles both simple fields and complex nested structures
- Lists of objects are represented with `[]` in the path notation
- Keys in the blacklist are excluded regardless of their nesting level
- Circular references are safely handled to prevent infinite loops
- Works with optional fields and primitive types