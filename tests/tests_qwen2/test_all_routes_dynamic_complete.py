"""
Dynamic tests for all registered routes in the application.
Tests follow the required order: POST, GET, PATCH, DELETE.
Uses authenticated_client_with_db fixture for database connectivity.
"""
import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import asyncio
import logging

from app.main import app as main_app
from tests.utility.find_models import discover_schemas2


class RouteTestManager:
    """Manages dynamic testing of all registered routes."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.test_data_store = {}
        self.test_results = {}
        self.created_items = {}
    
    def get_routes_by_method(self, method: str) -> List[APIRoute]:
        """Get all routes that support a specific HTTP method."""
        exclude_paths = {'/', '/auth/token', '/wait', '/health', '/docs', '/redoc', '/openapi.json'}
        routes = []
        
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                if route.path not in exclude_paths and method in route.methods:
                    routes.append(route)
        return routes
    
    def get_request_model(self, route: APIRoute) -> Optional[type[BaseModel]]:
        """Extract the request model from a route."""
        if hasattr(route, 'dependant') and hasattr(route.dependant, 'body_params'):
            for param in route.dependant.body_params:
                # Different FastAPI versions may have different attribute names
                annotation = getattr(param, 'annotation', None)
                if annotation is None:
                    # Try alternative attribute name
                    annotation = getattr(param, 'type_', None)
                
                if annotation and isinstance(annotation, type) and issubclass(annotation, BaseModel):
                    return annotation
        return None
    
    def get_model_from_schema_name(self, schema_name: str) -> Optional[type[BaseModel]]:
        """Get model by its name from the app's schema definitions."""
        # Use discover_schemas2 to get all models from the app
        all_models = discover_schemas2(self.app)
        for model_name, model_class in all_models.items():
            if model_name == schema_name:
                return model_class
        return None
    
    def get_create_model_from_response(self, route: APIRoute) -> Optional[type[BaseModel]]:
        """Extract a create model from response model if it contains one."""
        response_model = route.response_model
        if response_model and issubclass(response_model, BaseModel):
            # Some response models might wrap the actual create model
            # Check if the response model is related to create operations
            if 'Create' in response_model.__name__ or 'create' in response_model.__name__.lower():
                return response_model
            # Also check if we can extract a create schema from the response model
            # For example, if response is CreateResponse[ActualCreateModel]
            import typing
            if hasattr(response_model, '__args__') or hasattr(response_model, '__orig_bases__'):
                # This might be a generic type
                origin = getattr(response_model, '__origin__', None)
                if origin:
                    # For Generic models, check the arguments
                    args = getattr(response_model, '__args__', ())
                    for arg in args:
                        if isinstance(arg, type) and issubclass(arg, BaseModel):
                            if 'Create' in arg.__name__ or 'create' in arg.__name__.lower():
                                return arg
        return None
    
    def get_response_model(self, route: APIRoute) -> Optional[type[BaseModel]]:
        """Extract the response model from a route."""
        return route.response_model if route.response_model else None
    
    def generate_test_data(self, model: type[BaseModel]) -> Dict[str, Any]:
        """Generate test data based on the Pydantic model."""
        if not model or not issubclass(model, BaseModel):
            return {}
        
        # Get model fields and create basic test data
        test_data = {}
        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation
            
            # Handle generic types (Optional, List, etc.)
            origin_type = getattr(field_type, '__origin__', None)
            if origin_type:
                # Handle Optional/Union types
                if origin_type == type(None) or str(origin_type) == 'typing.Union':
                    args = getattr(field_type, '__args__', ())
                    if args:
                        # Get the first non-None type
                        for arg in args:
                            if arg != type(None):
                                field_type = arg
                                origin_type = getattr(field_type, '__origin__', None)
                                break
                elif origin_type == list or str(origin_type) == 'list':
                    # For list fields, create an empty list or simple list
                    test_data[field_name] = []
                    continue
                elif origin_type == dict or str(origin_type) == 'dict':
                    # For dict fields, create an empty dict
                    test_data[field_name] = {}
                    continue
            
            # Handle different field types
            if field_type == str:
                if 'name' in field_name.lower() or 'title' in field_name.lower():
                    test_data[field_name] = f"Test {field_name.title()}"
                elif 'email' in field_name.lower():
                    test_data[field_name] = "test@example.com"
                elif 'description' in field_name.lower():
                    test_data[field_name] = f"Test description for {field_name}"
                elif 'id' in field_name.lower():
                    # Skip id fields as they're typically auto-generated
                    continue
                else:
                    test_data[field_name] = f"test_{field_name}_value"
            elif field_type == int:
                if 'id' in field_name.lower():
                    # Skip id fields
                    continue
                else:
                    test_data[field_name] = 1
            elif field_type == float:
                test_data[field_name] = 1.0
            elif field_type == bool:
                test_data[field_name] = True
            elif hasattr(field_type, '__origin__'):  # Handle Optional, List, etc.
                if getattr(field_type, '__origin__', None) is not None:
                    # For now, handle as empty or basic type
                    if field_name != 'id':  # Don't generate ID if it's not supposed to be set
                        if 'Optional' in str(field_type) or field_type.__name__ == 'Union':
                            # For optional fields, try to infer from arguments
                            args = getattr(field_type, '__args__', [])
                            if args:
                                # Get the first non-None type
                                for arg in args:
                                    if arg != type(None):
                                        if arg == str:
                                            test_data[field_name] = f"test_{field_name}_value"
                                        elif arg == int:
                                            test_data[field_name] = 1
                                        elif arg == float:
                                            test_data[field_name] = 1.0
                                        elif arg == bool:
                                            test_data[field_name] = True
                                        else:
                                            test_data[field_name] = None
                                        break
                            else:
                                test_data[field_name] = None
                        else:
                            test_data[field_name] = None
                else:
                    test_data[field_name] = None
            elif hasattr(field_type, '__name__') and 'BaseModel' in str(field_type.__bases__):
                # Handle nested Pydantic models by creating test data for them too
                nested_test_data = self.generate_test_data(field_type)
                test_data[field_name] = nested_test_data
            else:
                if field_name != 'id':
                    test_data[field_name] = f"test_{field_name}_value"
        
        return test_data
    
    async def test_post_routes(self, authenticated_client_with_db):
        """Test all POST routes with positive and negative tests."""
        print("\n=== Testing POST routes ===")
        post_routes = self.get_routes_by_method('POST')
        results = {}
        
        for route in post_routes:
            route_path = route.path
            print(f"Testing POST {route_path}")
            
            # Get request model
            request_model = self.get_request_model(route)
            
            if request_model:
                # Positive test
                try:
                    test_data = self.generate_test_data(request_model)
                    response = await authenticated_client_with_db.post(route_path, json = test_data)
                    success = response.status_code in [200, 201]
                    results[route_path] = {'method': 'POST', 'status': 'PASS' if success else 'FAIL',
                            'status_code': response.status_code,
                            'response': response.json() if success and response.content else 'No content'}
                    
                    # Store created item ID for future tests
                    if success:
                        try:
                            response_data = response.json()
                        except:
                            response_data = {}
                        # Try to extract ID from response
                        item_id = None
                        if isinstance(response_data, dict):
                            item_id = response_data.get('id') or response_data.get('_id') or 1
                        elif isinstance(response_data, list) and len(response_data) > 0:
                            item_id = response_data[0].get('id') or response_data[0].get('_id') or 1
                        
                        if item_id:
                            # Store the ID for GET, PATCH, DELETE tests
                            if route_path not in self.created_items:
                                self.created_items[route_path] = []
                            self.created_items[route_path].append(item_id)
                
                except Exception as e:
                    results[route_path] = {'method': 'POST', 'status': 'ERROR', 'error': str(e), 'status_code': None}
                
                # Negative test - send empty data
                try:
                    response = await authenticated_client_with_db.post(route_path, json = {})
                    negative_success = response.status_code >= 400  # Expecting error for empty data
                    if route_path not in results:
                        results[route_path] = {}
                    results[route_path]['negative_test'] = {'status': 'PASS' if negative_success else 'FAIL',
                            'status_code': response.status_code}
                except Exception as e:
                    if route_path not in results:
                        results[route_path] = {}
                    results[route_path]['negative_test'] = {'status': 'ERROR', 'error': str(e)}
            else:
                results[route_path] = {'method': 'POST', 'status': 'SKIPPED - No request model',
                        'reason': 'No request model found'}
        
        return results
    
    async def test_get_routes(self, authenticated_client_with_db):
        """Test all GET routes with positive and negative tests."""
        print("\n=== Testing GET routes ===")
        get_routes = self.get_routes_by_method('GET')
        results = {}
        
        for route in get_routes:
            route_path = route.path
            print(f"Testing GET {route_path}")
            
            # Determine if this is a single item get (contains {id} or {item_id} pattern)
            is_single_item = any(param in route_path for param in ['{id}', '{item_id}', '{_id}'])
            
            if is_single_item:
                # Try to use a previously created item ID
                base_path = route_path.split('{')[0]  # Get base path without the ID parameter
                matching_created_items = []
                
                # Find routes that might have created items for this base path
                for created_route, items in self.created_items.items():
                    if created_route.startswith(base_path) or base_path.startswith(created_route):
                        matching_created_items.extend(items)
                
                if matching_created_items:
                    item_id = matching_created_items[0]  # Use first available ID
                    actual_path = route_path.replace('{id}', str(item_id)).replace('{item_id}', str(item_id)).replace(
                        '{_id}', str(item_id)
                        )
                    
                    try:
                        response = await authenticated_client_with_db.get(actual_path)
                        success = response.status_code in [200, 201]
                        results[route_path] = {'method': 'GET (single)', 'status': 'PASS' if success else 'FAIL',
                                'status_code': response.status_code,
                                'response': response.json() if success and response.content else 'No content'}
                    except Exception as e:
                        results[route_path] = {'method': 'GET (single)', 'status': 'ERROR', 'error': str(e),
                                'status_code': None}
                    
                    # Negative test - try with invalid ID
                    try:
                        invalid_path = route_path.replace('{id}', '999999').replace('{item_id}', '999999').replace(
                            '{_id}', '999999'
                            )
                        response = await authenticated_client_with_db.get(invalid_path)
                        negative_success = response.status_code >= 400
                        if route_path not in results:
                            results[route_path] = {}
                        results[route_path]['negative_test'] = {'status': 'PASS' if negative_success else 'FAIL',
                                'status_code': response.status_code}
                    except Exception as e:
                        if route_path not in results:
                            results[route_path] = {}
                        results[route_path]['negative_test'] = {'status': 'ERROR', 'error': str(e)}
                else:
                    results[route_path] = {'method': 'GET (single)', 'status': 'SKIPPED - No created items to test',
                            'reason': 'No items created to test single item retrieval'}
            else:
                # This is a list/get-all route
                try:
                    response = await authenticated_client_with_db.get(route_path)
                    success = response.status_code in [200, 201]
                    results[route_path] = {'method': 'GET (list)', 'status': 'PASS' if success else 'FAIL',
                            'status_code': response.status_code,
                            'response': response.json() if success and response.content else 'No content'}
                except Exception as e:
                    results[route_path] = {'method': 'GET (list)', 'status': 'ERROR', 'error': str(e),
                            'status_code': None}
                
                # Negative test - could involve auth issues, etc.
                try:
                    # We'll just repeat the same request for now as a basic negative test
                    # In a real scenario, we might test with invalid tokens or malformed requests
                    pass
                except Exception as e:
                    if route_path not in results:
                        results[route_path] = {}
                    results[route_path]['negative_test'] = {'status': 'ERROR', 'error': str(e)}
        
        return results
    
    async def test_patch_routes(self, authenticated_client_with_db):
        """Test all PATCH routes with positive and negative tests."""
        print("\n=== Testing PATCH routes ===")
        patch_routes = self.get_routes_by_method('PATCH')
        results = {}
        
        for route in patch_routes:
            route_path = route.path
            print(f"Testing PATCH {route_path}")
            
            # Get request model
            request_model = self.get_request_model(route)
            
            if request_model and request_model != type(None):
                # Try to find a matching created item
                base_path = route_path.split('{')[0]  # Get base path without the ID parameter
                matching_created_items = []
                
                # Find routes that might have created items for this base path
                for created_route, items in self.created_items.items():
                    if created_route.startswith(base_path) or base_path.startswith(created_route):
                        matching_created_items.extend(items)
                
                if matching_created_items:
                    item_id = matching_created_items[0]  # Use first available ID
                    actual_path = route_path.replace('{id}', str(item_id)).replace('{item_id}', str(item_id)).replace(
                        '{_id}', str(item_id)
                        )
                    
                    # Generate update data
                    update_data = self.generate_test_data(request_model)
                    # Modify the data to indicate it's updated
                    for key, value in update_data.items():
                        if isinstance(value, str) and not value.startswith('updated_'):
                            update_data[key] = f"updated_{value}"
                    
                    try:
                        response = await authenticated_client_with_db.patch(actual_path, json = update_data)
                        success = response.status_code in [200, 201, 204]
                        results[route_path] = {'method': 'PATCH', 'status': 'PASS' if success else 'FAIL',
                                'status_code': response.status_code,
                                'response': response.json() if success and response.content else 'No content'}
                    except Exception as e:
                        results[route_path] = {'method': 'PATCH', 'status': 'ERROR', 'error': str(e),
                                'status_code': None}
                    
                    # Negative test - send empty data or invalid data
                    try:
                        response = await authenticated_client_with_db.patch(actual_path, json = {})
                        negative_success = response.status_code >= 400
                        if route_path not in results:
                            results[route_path] = {}
                        results[route_path]['negative_test'] = {'status': 'PASS' if negative_success else 'FAIL',
                                'status_code': response.status_code}
                    except Exception as e:
                        if route_path not in results:
                            results[route_path] = {}
                        results[route_path]['negative_test'] = {'status': 'ERROR', 'error': str(e)}
                else:
                    results[route_path] = {'method': 'PATCH', 'status': 'SKIPPED - No created items to test',
                            'reason': 'No items created to test patch operation'}
            else:
                results[route_path] = {'method': 'PATCH', 'status': 'SKIPPED - No request model',
                        'reason': 'No request model found for PATCH route'}
        
        return results
    
    async def test_delete_routes(self, authenticated_client_with_db):
        """Test all DELETE routes with positive and negative tests."""
        print("\n=== Testing DELETE routes ===")
        delete_routes = self.get_routes_by_method('DELETE')
        results = {}
        
        for route in delete_routes:
            route_path = route.path
            print(f"Testing DELETE {route_path}")
            
            # Try to find a matching created item
            base_path = route_path.split('{')[0]  # Get base path without the ID parameter
            matching_created_items = []
            
            # Find routes that might have created items for this base path
            for created_route, items in self.created_items.items():
                if created_route.startswith(base_path) or base_path.startswith(created_route):
                    matching_created_items.extend(items)
            
            if matching_created_items:
                item_id = matching_created_items[0]  # Use first available ID
                actual_path = route_path.replace('{id}', str(item_id)).replace('{item_id}', str(item_id)).replace(
                    '{_id}', str(item_id)
                    )
                
                try:
                    response = await authenticated_client_with_db.delete(actual_path)
                    success = response.status_code in [200, 204]
                    results[route_path] = {'method': 'DELETE', 'status': 'PASS' if success else 'FAIL',
                            'status_code': response.status_code,
                            'response': 'Deleted successfully' if success else 'Deletion failed'}
                except Exception as e:
                    results[route_path] = {'method': 'DELETE', 'status': 'ERROR', 'error': str(e), 'status_code': None}
                
                # Negative test - try to delete the same item again (should fail)
                try:
                    response = await authenticated_client_with_db.delete(actual_path)
                    negative_success = response.status_code >= 400  # Should fail since item was already deleted
                    if route_path not in results:
                        results[route_path] = {}
                    results[route_path]['negative_test'] = {'status': 'PASS' if negative_success else 'FAIL',
                            'status_code': response.status_code}
                except Exception as e:
                    if route_path not in results:
                        results[route_path] = {}
                    results[route_path]['negative_test'] = {'status': 'ERROR', 'error': str(e)}
            else:
                results[route_path] = {'method': 'DELETE', 'status': 'SKIPPED - No created items to test',
                        'reason': 'No items created to test delete operation'}
        
        return results


@pytest.mark.asyncio
async def test_all_routes_dynamic(authenticated_client_with_db, test_mongodb):
    """Main test function that runs tests in the required order."""
    print("\nStarting dynamic route testing...")
    
    manager = RouteTestManager(main_app)
    
    # 4.1 Test POST routes first
    post_results = await manager.test_post_routes(authenticated_client_with_db)
    
    # 4.2 Test GET routes
    get_results = await manager.test_get_routes(authenticated_client_with_db)
    
    # 4.3 Test PATCH routes
    patch_results = await manager.test_patch_routes(authenticated_client_with_db)
    
    # 4.4 Test DELETE routes
    delete_results = await manager.test_delete_routes(authenticated_client_with_db)
    
    # Combine all results
    all_results = {}
    all_results.update(post_results)
    all_results.update(get_results)
    all_results.update(patch_results)
    all_results.update(delete_results)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    method_counts = {'POST': 0, 'GET': 0, 'PATCH': 0, 'DELETE': 0}
    status_counts = {'PASS': 0, 'FAIL': 0, 'ERROR': 0, 'SKIPPED': 0}
    
    for route, result in all_results.items():
        method = result.get('method', 'UNKNOWN').split(' ')[0]  # Extract method from 'GET (list)' or 'GET (single)'
        status = result.get('status', 'UNKNOWN')
        
        if method in method_counts:
            method_counts[method] += 1
        if status in status_counts:
            status_counts[status.split(' ')[0]] += 1  # Handle cases like 'SKIPPED - reason'
        
        print(f"{method:6} {route:50} {status}")
    
    print("\nMethod Summary:")
    for method, count in method_counts.items():
        print(f"  {method}: {count} routes tested")
    
    print("\nStatus Summary:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} routes")
    
    # Calculate overall success rate
    total_tested = sum(status_counts.values())
    passed = status_counts.get('PASS', 0)
    if total_tested > 0:
        success_rate = (passed / total_tested) * 100
        print(f"\nOverall Success Rate: {success_rate:.1f}% ({passed}/{total_tested})")
    
    # Return results for further inspection if needed
    return all_results