# app/core/utils/pydantic_key_extractor.py
from typing import List, Any, Union, get_origin, get_args
from pydantic import BaseModel
from pydantic.fields import FieldInfo


def extract_keys_with_blacklist(schema: type,
                                blacklist: List[str] = ['vol', 'alc', 'price', 'id', 'updated_at', 'created_at', 'count']
                                ) -> List[str]:
    """
    Extracts all key paths from a Pydantic schema with dot notation for full depth of nesting,
    excluding keys that have values in the blacklist at any level of nesting.

    Args:
        schema: Pydantic model class
        blacklist: List of keys to exclude from the result

    Returns:
        List of key paths in dot notation
    """
    result = []
    visited_types = set()  # Keep track of visited types to prevent infinite recursion

    def _extract_keys_recursive(model_type: type, current_path: str = ""):
        # Prevent circular reference issues
        type_repr = repr(model_type)
        if type_repr in visited_types:
            return
        visited_types.add(type_repr)

        # Check if the model_type is a Pydantic model (Pydantic v2 style)
        if hasattr(model_type, 'model_fields'):
            fields = model_type.model_fields
            for field_name, field_info in fields.items():
                # Skip if field name is in blacklist
                if field_name in blacklist:
                    continue

                field_path = f"{current_path}.{field_name}" if current_path else field_name

                # Get the annotation/field type
                field_type = field_info.annotation if isinstance(field_info, FieldInfo) else field_info

                # Handle list types
                if get_origin(field_type) is list or get_origin(field_type) is List:
                    args = get_args(field_type)
                    if args:
                        item_type = args[0]
                        # Add the path for the list itself
                        result.append(field_path)
                        # Process the item type recursively (avoiding circular refs)
                        _extract_keys_recursive(item_type, f"{field_path}[]")
                elif hasattr(field_type, 'model_fields') or (
                        hasattr(field_type, '__annotations__') and issubclass(field_type, BaseModel)):
                    # Add the current field path
                    result.append(field_path)
                    # Recursively process nested models
                    _extract_keys_recursive(field_type, field_path)
                else:
                    # Add simple field
                    result.append(field_path)

        # Handle regular Python classes/types that might have attributes
        elif hasattr(model_type, '__annotations__'):
            annotations = model_type.__annotations__
            for field_name, field_type in annotations.items():
                # Skip if field name is in blacklist
                if field_name in blacklist:
                    continue

                field_path = f"{current_path}.{field_name}" if current_path else field_name

                # Handle list types
                if get_origin(field_type) is list or get_origin(field_type) is List:
                    args = get_args(field_type)
                    if args:
                        item_type = args[0]
                        # Add the path for the list itself
                        result.append(field_path)
                        # Process the item type recursively (avoiding circular refs)
                        _extract_keys_recursive(item_type, f"{field_path}[]")
                elif hasattr(field_type, 'model_fields') or (
                        hasattr(field_type, '__annotations__') and issubclass(type(field_type), BaseModel)):
                    # Add the current field path
                    result.append(field_path)
                    # Recursively process nested models
                    _extract_keys_recursive(field_type, field_path)
                else:
                    # Add simple field
                    result.append(field_path)

    # Start the recursive extraction
    _extract_keys_recursive(schema)

    return result


# Example usage:
if __name__ == "__main__":
    from pydantic import BaseModel
    from typing import List, Optional

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
        tags: List[str]

    # Define blacklist
    blacklist = ['email', 'country']

    # Extract keys
    keys = extract_keys_with_blacklist(User, blacklist)
    print("Extracted keys:", keys)
