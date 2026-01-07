"""
Analysis of all registered routes in the application.
This script analyzes the routes and prints information about them.
"""
from fastapi import FastAPI
from fastapi.routing import APIRoute
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import inspect
from app.main import app as main_app
from tests.utility.find_models import discover_schemas2


def analyze_routes():
    """Analyze all routes in the application."""
    print("Analyzing routes in the application...")
    
    # Get all routes
    all_routes = []
    for route in main_app.routes:
        if isinstance(route, APIRoute):
            all_routes.append(route)
    
    print(f"Found {len(all_routes)} API routes:")
    
    # Group by method
    methods = {'GET': [], 'POST': [], 'PATCH': [], 'DELETE': [], 'PUT': [], 'HEAD': [], 'OPTIONS': [], 'TRACE': []}
    
    for route in all_routes:
        for method in route.methods:
            if method in methods:
                methods[method].append(route)
            else:
                print(f"  Unknown method: {method} for route {route.path}")
    
    print("\nRoutes by method:")
    for method, routes in methods.items():
        if routes:  # Only show methods that have routes
            print(f"\n  {method}: {len(routes)} routes")
            for route in routes:
                print(f"    - {route.path} -> {getattr(route, 'name', 'unnamed')}")
                
                # Try to get the request model
                request_model = get_request_model_from_route(route)
                if request_model:
                    print(f"      Request model: {request_model.__name__}")
                
                # Try to get the response model
                if route.response_model:
                    print(f"      Response model: {route.response_model.__name__}")
    
    return all_routes


def get_request_model_from_route(route: APIRoute) -> Optional[type[BaseModel]]:
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


def analyze_schemas():
    """Analyze all discovered schemas in the application."""
    print("\nAnalyzing schemas in the application...")
    
    all_schemas = discover_schemas2(main_app)
    print(f"Found {len(all_schemas)} schemas:")
    
    for schema_name, schema_class in all_schemas.items():
        print(f"  - {schema_name}: {schema_class}")
        
        # Print fields if it's a Pydantic model
        if hasattr(schema_class, 'model_fields'):
            print(f"    Fields: {list(schema_class.model_fields.keys())}")


if __name__ == "__main__":
    print("="*60)
    print("ROUTE ANALYSIS REPORT")
    print("="*60)
    
    routes = analyze_routes()
    
    print("\n" + "="*60)
    print("SCHEMA ANALYSIS REPORT")
    print("="*60)
    
    analyze_schemas()
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)