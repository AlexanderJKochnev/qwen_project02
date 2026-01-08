import pytest
import asyncio
from fastapi import FastAPI
from fastapi.routing import APIRoute
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import time
from concurrent.futures import ThreadPoolExecutor
import logging

from app.main import app as main_app
from tests.utility.find_models import discover_schemas2


class OptimizedRouteTestManager:
    """Optimized manager for testing all registered routes with performance improvements."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.test_data_store = {}
        self.created_items = {}
        self.timeout_per_request = 10  # seconds
        self.max_concurrent_requests = 10  # limit concurrent requests

    def get_routes_by_method(self, method: str) -> List[APIRoute]:
        """Get all routes that support a specific HTTP method."""
        exclude_paths = {'/', '/auth/token', '/wait', '/health', '/docs', '/redoc', '/openapi.json'}
        routes = []

        for route in self.app.routes:
            if isinstance(route, APIRoute):
                if route.path not in exclude_paths and method in route.methods:
                    routes.append(route)
        return routes

    def generate_basic_test_data(self, path: str) -> Dict[str, Any]:
        """Generate basic test data based on path pattern."""
        # Extract entity name from path
        path_parts = path.strip('/').split('/')
        entity_name = path_parts[-1] if path_parts else "entity"

        # Create basic test data based on common patterns
        test_data = {"name": f"test_{entity_name}", "description": f"Test {entity_name} description"}

        # Add specific fields based on path patterns
        if 'user' in entity_name.lower():
            test_data.update(
                {"username": f"test_user_{int(time.time())}",
                 "email": f"test_{entity_name}_{int(time.time())}@example.com"}
            )
        elif 'category' in entity_name.lower():
            test_data.update({"slug": f"test-{entity_name}"})
        elif 'country' in entity_name.lower():
            test_data.update({"code": "XX"})
        elif 'drink' in entity_name.lower():
            test_data.update(
                {"price": 10.99, "volume": 750}
            )

        return test_data

    async def safe_request(self, client, method: str, url: str, **kwargs):
        """Make a request with timeout protection."""
        try:
            # Use asyncio.wait_for to implement timeout
            response = await asyncio.wait_for(
                getattr(client, method.lower())(url, **kwargs), timeout=self.timeout_per_request
            )
            return {'status_code': response.status_code, 'json': response.json() if response.content else {},
                    'success': True}
        except asyncio.TimeoutError:
            return {'status_code': None, 'json': {}, 'success': False, 'error': 'timeout'}
        except Exception as e:
            return {'status_code': None, 'json': {}, 'success': False, 'error': str(e)}

    async def test_post_routes(self, authenticated_client_with_db):
        """Test all POST routes with positive and negative tests."""
        print("\n=== Testing POST routes ===")
        post_routes = self.get_routes_by_method('POST')
        results = {}

        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def test_single_post(route):
            async with semaphore:
                route_path = route.path
                print(f"Testing POST {route_path}")

                # Generate basic test data
                test_data = self.generate_basic_test_data(route_path)

                # Positive test
                pos_result = await self.safe_request(
                    authenticated_client_with_db, 'POST', route_path, json=test_data
                )

                success = pos_result['success'] and pos_result['status_code'] in [200, 201]
                results[route_path] = {'method': 'POST', 'status': 'PASS' if success else 'FAIL',
                                       'status_code': pos_result['status_code'], 'response': pos_result.get('json', {})}

                # Store created item ID for future tests
                if success and pos_result.get('json'):
                    response_data = pos_result['json']
                    # Try to extract ID from response
                    item_id = None
                    if isinstance(response_data, dict):
                        item_id = response_data.get('id') or response_data.get('_id')
                    elif isinstance(response_data, list) and len(response_data) > 0:
                        item_id = response_data[0].get('id') or response_data[0].get('_id')

                    if item_id:
                        # Store the ID for GET, PATCH, DELETE tests
                        if route_path not in self.created_items:
                            self.created_items[route_path] = []
                        self.created_items[route_path].append(item_id)

                # Negative test - send empty data
                neg_result = await self.safe_request(
                    authenticated_client_with_db, 'POST', route_path, json={}
                )
                negative_success = neg_result['success'] and neg_result['status_code'] >= 400

                results[route_path]['negative_test'] = {'status': 'PASS' if negative_success else 'FAIL',
                                                        'status_code': neg_result['status_code']}

        tasks = [test_single_post(route) for route in post_routes]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def test_get_routes(self, authenticated_client_with_db):
        """Test all GET routes with positive and negative tests."""
        print("\n=== Testing GET routes ===")
        get_routes = self.get_routes_by_method('GET')
        results = {}

        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def test_single_get(route):
            async with semaphore:
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
                        actual_path = route_path.replace('{id}', str(item_id)).replace(
                            '{item_id}', str(item_id)
                        ).replace('{_id}', str(item_id))

                        result = await self.safe_request(authenticated_client_with_db, 'GET', actual_path)
                        success = result['success'] and result['status_code'] in [200, 201]
                        results[route_path] = {'method': 'GET (single)', 'status': 'PASS' if success else 'FAIL',
                                               'status_code': result['status_code'], 'response': result.get('json', {})}

                        # Negative test - try with invalid ID
                        invalid_path = route_path.replace('{id}', '999999').replace('{item_id}', '999999').replace(
                            '{_id}', '999999'
                        )
                        neg_result = await self.safe_request(authenticated_client_with_db, 'GET', invalid_path)
                        negative_success = neg_result['success'] and neg_result['status_code'] >= 400
                        results[route_path]['negative_test'] = {'status': 'PASS' if negative_success else 'FAIL',
                                                                'status_code': neg_result['status_code']}
                    else:
                        results[route_path] = {'method': 'GET (single)', 'status': 'SKIPPED - No created items to test',
                                               'reason': 'No items created to test single item retrieval'}
                else:
                    # This is a list/get-all route
                    result = await self.safe_request(authenticated_client_with_db, 'GET', route_path)
                    success = result['success'] and result['status_code'] in [200, 201]
                    results[route_path] = {'method': 'GET (list)', 'status': 'PASS' if success else 'FAIL',
                                           'status_code': result['status_code'], 'response': result.get('json', {})}

        tasks = [test_single_get(route) for route in get_routes]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def test_patch_routes(self, authenticated_client_with_db):
        """Test all PATCH routes with positive and negative tests."""
        print("\n=== Testing PATCH routes ===")
        patch_routes = self.get_routes_by_method('PATCH')
        results = {}

        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def test_single_patch(route):
            async with semaphore:
                route_path = route.path
                print(f"Testing PATCH {route_path}")

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
                    update_data = self.generate_basic_test_data(route_path)
                    # Modify the data to indicate it's updated
                    for key, value in update_data.items():
                        if isinstance(value, str):
                            update_data[key] = f"updated_{value}"

                    # Positive test
                    pos_result = await self.safe_request(
                        authenticated_client_with_db, 'PATCH', actual_path, json=update_data
                    )
                    success = pos_result['success'] and pos_result['status_code'] in [200, 201, 204]
                    results[route_path] = {'method': 'PATCH', 'status': 'PASS' if success else 'FAIL',
                                           'status_code': pos_result['status_code'], 'response': pos_result.get('json', {})}

                    # Negative test - send empty data
                    neg_result = await self.safe_request(
                        authenticated_client_with_db, 'PATCH', actual_path, json={}
                    )
                    negative_success = neg_result['success'] and neg_result['status_code'] >= 400
                    results[route_path]['negative_test'] = {'status': 'PASS' if negative_success else 'FAIL',
                                                            'status_code': neg_result['status_code']}
                else:
                    results[route_path] = {'method': 'PATCH', 'status': 'SKIPPED - No created items to test',
                                           'reason': 'No items created to test patch operation'}

        tasks = [test_single_patch(route) for route in patch_routes]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def test_delete_routes(self, authenticated_client_with_db):
        """Test all DELETE routes with positive and negative tests."""
        print("\n=== Testing DELETE routes ===")
        delete_routes = self.get_routes_by_method('DELETE')
        results = {}

        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def test_single_delete(route):
            async with semaphore:
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

                    # Positive test
                    pos_result = await self.safe_request(
                        authenticated_client_with_db, 'DELETE', actual_path
                    )
                    success = pos_result['success'] and pos_result['status_code'] in [200, 204]
                    results[route_path] = {'method': 'DELETE', 'status': 'PASS' if success else 'FAIL',
                                           'status_code': pos_result['status_code'],
                                           'response': 'Deleted successfully' if success else 'Deletion failed'}

                    # Negative test - try to delete the same item again (should fail)
                    neg_result = await self.safe_request(
                        authenticated_client_with_db, 'DELETE', actual_path
                    )
                    negative_success = neg_result['success'] and neg_result['status_code'] >= 400
                    results[route_path]['negative_test'] = {'status': 'PASS' if negative_success else 'FAIL',
                                                            'status_code': neg_result['status_code']}
                else:
                    results[route_path] = {'method': 'DELETE', 'status': 'SKIPPED - No created items to test',
                                           'reason': 'No items created to test delete operation'}

        tasks = [test_single_delete(route) for route in delete_routes]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results


@pytest.mark.asyncio
async def test_all_routes_dynamic_optimized(authenticated_client_with_db, test_mongodb):
    """Main test function that runs tests in the required order with optimizations."""
    print("\nStarting optimized dynamic route testing...")
    start_time = time.time()

    manager = OptimizedRouteTestManager(main_app)

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
    print("OPTIMIZED TEST RESULTS SUMMARY")
    print("=" * 60)

    method_counts = {'POST': 0, 'GET': 0, 'PATCH': 0, 'DELETE': 0}
    status_counts = {'PASS': 0, 'FAIL': 0, 'ERROR': 0, 'SKIPPED': 0}

    for route, result in all_results.items():
        method = result.get('method', 'UNKNOWN').split(' ')[0]  # Extract method from 'GET (list)' or 'GET (single)'
        status = result.get('status', 'UNKNOWN').split(' ')[0]  # Extract status from 'PASS', 'FAIL', etc.

        if method in method_counts:
            method_counts[method] += 1
        if status in status_counts:
            status_counts[status] += 1

        print(f"{method:6} {route:50} {result.get('status', 'UNKNOWN')}")

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

    elapsed_time = time.time() - start_time
    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")

    # Return results for further inspection if needed
    return all_results
