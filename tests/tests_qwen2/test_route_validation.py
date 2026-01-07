"""
Validation test to ensure the route discovery and test logic works correctly.
This test validates the core functionality without requiring full database connections.
"""
import pytest
from fastapi.routing import APIRoute
from app.main import app
from tests.tests_qwen2.test_all_routes_dynamic import RouteTestManager


def test_route_discovery():
    """Test that route discovery works correctly."""
    manager = RouteTestManager(app)
    
    # Test that we can discover routes by method
    post_routes = manager.get_routes_by_method('POST')
    get_routes = manager.get_routes_by_method('GET')
    patch_routes = manager.get_routes_by_method('PATCH')
    delete_routes = manager.get_routes_by_method('DELETE')
    
    print(f"Discovered {len(post_routes)} POST routes")
    print(f"Discovered {len(get_routes)} GET routes")  
    print(f"Discovered {len(patch_routes)} PATCH routes")
    print(f"Discovered {len(delete_routes)} DELETE routes")
    
    # Verify that we found routes for each method
    assert len(post_routes) > 0, "Should find at least one POST route"
    assert len(get_routes) > 0, "Should find at least one GET route"
    assert len(patch_routes) > 0, "Should find at least one PATCH route"
    assert len(delete_routes) > 0, "Should find at least one DELETE route"
    
    # Check that some routes have request models
    routes_with_models = 0
    for route in post_routes:
        model = manager.get_request_model(route)
        if model:
            routes_with_models += 1
    
    print(f"Found {routes_with_models} POST routes with request models")
    assert routes_with_models > 0, "Should find at least one POST route with a request model"
    
    # Test data generation for a sample model
    sample_post_route = post_routes[0] if post_routes else None
    if sample_post_route:
        request_model = manager.get_request_model(sample_post_route)
        if request_model:
            test_data = manager.generate_test_data(request_model)
            print(f"Generated test data for {request_model.__name__}: {test_data}")
            assert isinstance(test_data, dict), "Generated test data should be a dictionary"
    
    print("✓ Route discovery and test data generation working correctly")


def test_route_filtering():
    """Test that route filtering excludes system routes."""
    manager = RouteTestManager(app)
    
    all_routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            all_routes.append(route)
    
    # Test that excluded paths are properly filtered
    post_routes = manager.get_routes_by_method('POST')
    get_routes = manager.get_routes_by_method('GET')
    
    # Ensure system routes are excluded
    for route in post_routes + get_routes:
        assert route.path not in {'/', '/auth/token', '/wait', '/health', '/docs', '/redoc', '/openapi.json'}, \
            f"System route {route.path} should be excluded"
    
    print("✓ Route filtering working correctly")


if __name__ == "__main__":
    test_route_discovery()
    test_route_filtering()
    print("All validation tests passed!")