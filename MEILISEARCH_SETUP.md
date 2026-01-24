# Meilisearch Initial Population Setup

## Overview
This project uses Meilisearch for advanced search capabilities. After creating the Meilisearch index, you need to populate it with existing data from the database.

## Features Added

### 1. Initial Data Population Method
- **Method**: `populate_index_from_db()` in `SearchService`
- **Purpose**: Populates the Meilisearch index with all existing items from the database
- **Usage**: Can be called manually or during application startup

### 2. Manual Population Script
- **Script**: `/workspace/populate_meilisearch.py`
- **Purpose**: Command-line script to manually populate the Meilisearch index
- **Usage**: `python populate_meilisearch.py`

### 3. Shell Script Macro
- **Script**: `/workspace/scripts/populate_meilisearch.sh`
- **Purpose**: Convenient shell script to run the population process
- **Usage**: `./scripts/populate_meilisearch.sh`

### 4. Dependency Injection Support
- **Integration**: Search service is now registered in the service registry
- **Access**: Via `get_service('search_service')` from the service registry
- **Lazy Loading**: Avoids circular import issues

### 5. Startup Configuration Option
- **Environment Variable**: `POPULATE_MEILISEARCH_ON_STARTUP=true`
- **Purpose**: Automatically populate the index when the application starts
- **Usage**: Set to "true" to enable initial population on startup

## Usage Examples

### Manual Population
```bash
# Run the Python script directly
python populate_meilisearch.py

# Or use the shell script
./scripts/populate_meilisearch.sh
```

### Programmatic Usage
```python
from app.core.services.search_service import search_service

# Initialize the index
await search_service.initialize_index()

# Populate with existing data
await search_service.populate_index_from_db(batch_size=100)
```

### Using Service Registry
```python
from app.service_registry import get_service

search_service = get_service('search_service')
await search_service.populate_index_from_db(batch_size=100)
```

### Startup with Auto-Population
```bash
# Set environment variable before starting the app
export POPULATE_MEILISEARCH_ON_STARTUP=true
uvicorn app.main:app --reload
```

## Architecture Changes

1. **Search Service Enhancement**:
   - Added `populate_index_from_db()` method
   - Properly loads all required relationships for indexing
   - Includes error handling and logging

2. **Service Registry Integration**:
   - Added lazy loading mechanism
   - Avoids circular import issues
   - Provides centralized service access

3. **Background Task Enhancement**:
   - Added optional initial population parameter
   - Maintains backward compatibility

## Notes
- The population method handles all related entities (Drink, Subcategory, Region, Country, etc.)
- Uses batching to efficiently process large datasets
- Includes comprehensive error handling and logging
- Maintains all existing functionality while adding new features