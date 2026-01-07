"""
Simple test to verify route discovery functionality
"""
from fastapi.routing import APIRoute
from app.main import app


def test_route_discovery():
    """Test that we can discover all routes properly."""
    print("Discovering routes...")
    
    # Get all routes
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(route)
    
    print(f"Found {len(routes)} API routes:")
    for route in routes:
        print(f"  {route.methods} {route.path} -> {route.name if hasattr(route, 'name') else 'unnamed'}")
    
    # Group by method
    methods = {'GET': [], 'POST': [], 'PATCH': [], 'DELETE': [], 'PUT': [], 'OTHER': []}
    
    for route in routes:
        for method in route.methods:
            if method in methods:
                methods[method].append(route.path)
            else:
                methods['OTHER'].append(route.path)
    
    print("\nRoutes by method:")
    for method, paths in methods.items():
        if paths:  # Only show methods that have routes
            print(f"  {method}: {len(paths)} routes")
            for path in paths:
                print(f"    - {path}")
    
    # Return for verification
    return routes


if __name__ == "__main__":
    test_route_discovery()