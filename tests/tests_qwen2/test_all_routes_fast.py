import pytest
import asyncio
from fastapi import FastAPI
from fastapi.routing import APIRoute
from typing import Dict, List, Any
import time
import random
from collections import defaultdict

from app.main import app as main_app


class FastRouteTestManager:
    """Fast manager for testing all registered routes with maximum performance."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.created_items = {}
        self.timeout_per_request = 5  # Reduced timeout
        self.max_concurrent_requests = 5  # Reduced concurrency to avoid DB overload
        self.test_results = {}

    def get_routes_by_method(self, method: str) -> List[APIRoute]:
        """Get all routes that support a specific HTTP method."""
        exclude_paths = {'/', '/auth/token', '/wait', '/health', '/docs', '/redoc', '/openapi.json'}
        routes = []

        for route in self.app.routes:
            if isinstance(route, APIRoute):
                if route.path not in exclude_paths and method in route.methods:
                    routes.append(route)
        return routes

    def get_unique_path_patterns(self, routes: List[APIRoute]) -> List[APIRoute]:
        """Group routes by similar patterns to reduce testing overhead."""
        patterns = {}
        for route in routes:
            # Create a pattern by replacing ID placeholders with a standard form
            pattern = route.path.replace('{id}', '<ID>').replace('{item_id}', '<ID>').replace('{_id}', '<ID>')
            if pattern not in patterns:
                patterns[pattern] = route
        return list(patterns.values())

    def generate_basic_test_data(self, path: str) -> Dict[str, Any]:
        """Generate minimal test data based on path pattern."""
        # Create minimal test data to reduce validation overhead
        timestamp = int(time.time() * 1000) % 100000  # Short unique identifier
        return {"name": f"test_{timestamp}", "description": f"Test data for {path.split('/')[-1]}"}

    async def make_request_with_timeout(self, client, method: str, url: str, json_data=None):
        """Make HTTP request with timeout."""
        try:
            coro = getattr(client, method.lower())(url, json=json_data)
            response = await asyncio.wait_for(coro, timeout=self.timeout_per_request)
            return {'status_code': response.status_code, 'content': response.content, 'success': True}
        except asyncio.TimeoutError:
            return {'status_code': None, 'content': b'', 'success': False, 'error': 'timeout'}
        except Exception as e:
            return {'status_code': None, 'content': b'', 'success': False, 'error': str(e)}

    async def test_post_routes(self, authenticated_client_with_db):
        """Test POST routes with minimal overhead."""
        print("\n=== Testing POST routes (fast) ===")
        all_post_routes = self.get_routes_by_method('POST')
        unique_post_routes = self.get_unique_path_patterns(all_post_routes)

        print(f"Testing {len(unique_post_routes)} unique POST patterns out of {len(all_post_routes)} total")

        results = {}
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def test_single_post(route):
            async with semaphore:
                route_path = route.path
                print(f"Testing POST {route_path}")

                # Generate minimal test data
                test_data = self.generate_basic_test_data(route_path)

                # Single positive test
                pos_result = await self.make_request_with_timeout(
                    authenticated_client_with_db, 'POST', route_path, test_data
                )

                success = pos_result['success'] and pos_result['status_code'] in [200, 201]
                results[route_path] = {'method': 'POST', 'status': 'PASS' if success else 'FAIL',
                                       'status_code': pos_result['status_code'], }

                # Store ID if creation was successful
                if success and pos_result['content']:
                    try:
                        import json
                        response_json = json.loads(pos_result['content'].decode('utf-8'))
                        item_id = None
                        if isinstance(response_json, dict):
                            item_id = response_json.get('id') or response_json.get('_id')
                        if item_id:
                            if route_path not in self.created_items:
                                self.created_items[route_path] = []
                            self.created_items[route_path].append(item_id)
                    except:
                        pass  # Ignore JSON parsing errors

        tasks = [test_single_post(route) for route in unique_post_routes]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def test_get_routes(self, authenticated_client_with_db):
        """Test GET routes efficiently."""
        print("\n=== Testing GET routes (fast) ===")
        all_get_routes = self.get_routes_by_method('GET')
        unique_get_routes = self.get_unique_path_patterns(all_get_routes)

        print(f"Testing {len(unique_get_routes)} unique GET patterns out of {len(all_get_routes)} total")

        results = {}
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def test_single_get(route):
            async with semaphore:
                route_path = route.path
                print(f"Testing GET {route_path}")

                # Determine if this is a single item route
                has_id_param = '{id}' in route_path or '{item_id}' in route_path or '{_id}' in route_path

                if has_id_param and self.created_items:
                    # Try to find matching created item
                    matching_base = next(
                        (base for base in self.created_items.keys() if
                         base.replace('{id}', '').replace('{item_id}', '').replace(
                            '{_id}', ''
                        ) in route_path.replace('{id}', '').replace('{item_id}', '').replace('{_id}', '')),
                        None
                    )

                    if matching_base and self.created_items[matching_base]:
                        item_id = self.created_items[matching_base][0]
                        actual_path = route_path.replace('{id}', str(item_id)).replace(
                            '{item_id}', str(item_id)
                        ).replace('{_id}', str(item_id))

                        result = await self.make_request_with_timeout(authenticated_client_with_db, 'GET', actual_path)
                        success = result['success'] and result['status_code'] in [200, 201]
                        results[route_path] = {'method': 'GET (single)', 'status': 'PASS' if success else 'FAIL',
                                               'status_code': result['status_code'], }
                    else:
                        # Just test the route without ID if no matching item exists
                        result = await self.make_request_with_timeout(
                            authenticated_client_with_db, 'GET', route_path.replace('{id}', '1').replace(
                                '{item_id}', '1'
                            ).replace('{_id}', '1')
                        )
                        results[route_path] = {'method': 'GET (single, mock id)',
                                               'status': 'PASS' if result['success'] else 'FAIL',
                                               'status_code': result['status_code'], }
                else:
                    # Regular list/get route
                    result = await self.make_request_with_timeout(authenticated_client_with_db, 'GET', route_path)
                    success = result['success'] and result['status_code'] in [200, 201]
                    results[route_path] = {'method': 'GET (list)', 'status': 'PASS' if success else 'FAIL',
                                           'status_code': result['status_code'], }

        tasks = [test_single_get(route) for route in unique_get_routes]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def test_patch_routes(self, authenticated_client_with_db):
        """Test PATCH routes efficiently."""
        print("\n=== Testing PATCH routes (fast) ===")
        all_patch_routes = self.get_routes_by_method('PATCH')
        unique_patch_routes = self.get_unique_path_patterns(all_patch_routes)

        print(f"Testing {len(unique_patch_routes)} unique PATCH patterns out of {len(all_patch_routes)} total")

        results = {}
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def test_single_patch(route):
            async with semaphore:
                route_path = route.path
                print(f"Testing PATCH {route_path}")

                # Find matching created item
                matching_base = next(
                    (base for base in self.created_items.keys() if
                     base.replace('{id}', '').replace('{item_id}', '').replace('{_id}', '') in route_path.replace(
                        '{id}', ''
                    ).replace('{item_id}', '').replace('{_id}', '')), None
                )

                if matching_base and self.created_items[matching_base]:
                    item_id = self.created_items[matching_base][0]
                    actual_path = route_path.replace('{id}', str(item_id)).replace('{item_id}', str(item_id)).replace(
                        '{_id}', str(item_id)
                    )

                    update_data = self.generate_basic_test_data(route_path)
                    update_data['name'] = f"updated_{update_data['name']}"

                    result = await self.make_request_with_timeout(
                        authenticated_client_with_db, 'PATCH', actual_path, update_data
                    )
                    success = result['success'] and result['status_code'] in [200, 201, 204]
                    results[route_path] = {'method': 'PATCH', 'status': 'PASS' if success else 'FAIL',
                                           'status_code': result['status_code'], }
                else:
                    results[route_path] = {'method': 'PATCH', 'status': 'SKIPPED - No items to update',
                                           'status_code': None, }

        tasks = [test_single_patch(route) for route in unique_patch_routes]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def test_delete_routes(self, authenticated_client_with_db):
        """Test DELETE routes efficiently."""
        print("\n=== Testing DELETE routes (fast) ===")
        all_delete_routes = self.get_routes_by_method('DELETE')
        unique_delete_routes = self.get_unique_path_patterns(all_delete_routes)

        print(f"Testing {len(unique_delete_routes)} unique DELETE patterns out of {len(all_delete_routes)} total")

        results = {}
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def test_single_delete(route):
            async with semaphore:
                route_path = route.path
                print(f"Testing DELETE {route_path}")

                # Find matching created item
                matching_base = next(
                    (base for base in self.created_items.keys() if
                     base.replace('{id}', '').replace('{item_id}', '').replace('{_id}', '') in route_path.replace(
                        '{id}', ''
                    ).replace('{item_id}', '').replace('{_id}', '')), None
                )

                if matching_base and self.created_items[matching_base]:
                    item_id = self.created_items[matching_base][0]
                    actual_path = route_path.replace('{id}', str(item_id)).replace('{item_id}', str(item_id)).replace(
                        '{_id}', str(item_id)
                    )

                    result = await self.make_request_with_timeout(
                        authenticated_client_with_db, 'DELETE', actual_path
                    )
                    success = result['success'] and result['status_code'] in [200, 204]
                    results[route_path] = {'method': 'DELETE', 'status': 'PASS' if success else 'FAIL',
                                           'status_code': result['status_code'], }
                else:
                    results[route_path] = {'method': 'DELETE', 'status': 'SKIPPED - No items to delete',
                                           'status_code': None, }

        tasks = [test_single_delete(route) for route in unique_delete_routes]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results


@pytest.mark.asyncio
async def test_all_routes_fast(authenticated_client_with_db, test_mongodb):
    """Fast test function that tests unique route patterns only."""
    print("\nStarting fast dynamic route testing...")
    start_time = time.time()

    manager = FastRouteTestManager(main_app)

    # Test unique route patterns instead of all routes
    post_results = await manager.test_post_routes(authenticated_client_with_db)
    get_results = await manager.test_get_routes(authenticated_client_with_db)
    patch_results = await manager.test_patch_routes(authenticated_client_with_db)
    delete_results = await manager.test_delete_routes(authenticated_client_with_db)

    # Combine all results
    all_results = {}
    all_results.update(post_results)
    all_results.update(get_results)
    all_results.update(patch_results)
    all_results.update(delete_results)

    # Print summary
    print("\n" + "=" * 60)
    print("FAST TEST RESULTS SUMMARY")
    print("=" * 60)

    method_counts = defaultdict(int)
    status_counts = defaultdict(int)

    for route, result in all_results.items():
        method = result.get('method', 'UNKNOWN').split(' ')[0]
        status = result.get('status', 'UNKNOWN').split(' ')[0]

        method_counts[method] += 1
        status_counts[status] += 1

        print(f"{method:6} {route:50} {result.get('status', 'UNKNOWN')}")

    print("\nMethod Summary:")
    for method, count in method_counts.items():
        print(f"  {method}: {count} routes tested")

    print("\nStatus Summary:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} routes")

    # Calculate overall metrics
    total_tested = sum(status_counts.values())
    passed = status_counts.get('PASS', 0)
    if total_tested > 0:
        success_rate = (passed / total_tested) * 100
        print(f"\nOverall Success Rate: {success_rate:.1f}% ({passed}/{total_tested})")

    elapsed_time = time.time() - start_time
    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")

    # Show original vs tested route counts
    all_routes = [route for route in main_app.routes if isinstance(route, APIRoute)]
    exclude_paths = {'/', '/auth/token', '/wait', '/health', '/docs', '/redoc', '/openapi.json'}
    filtered_routes = [route for route in all_routes if route.path not in exclude_paths]

    method_totals = defaultdict(int)
    for route in filtered_routes:
        for method in route.methods:
            method_totals[method] += 1

    print(f"\nOriginal route counts:")
    for method, count in sorted(method_totals.items()):
        print(f"  {method}: {count} routes")

    print(f"\nRoutes tested (unique patterns only): {len(all_results)}")
    print(f"Routes skipped due to pattern grouping: {sum(method_totals.values()) - len(all_results)}")

    return all_results
