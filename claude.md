# SNUGeoSHM - Offshore Wind Turbine Monitoring Dashboard

## Project Overview

This is a Dash-based web application for monitoring offshore wind turbines through digital twin technology. The application integrates multiple geological, structural, and sensor analysis tools to provide comprehensive monitoring capabilities.

## Architecture

### Multi-Page Application Structure

The application uses Dash's multi-page architecture with the following organization:

```
SNUGeoSHM/
├── app.py                    # Main application entry point
├── common/                   # Shared utilities and components
│   ├── constants.py         # Global constants
│   ├── navbar.py            # Navigation bar component
│   └── utils.py             # Shared utility functions
├── pages/                   # Page modules (auto-registered)
│   ├── home/               # Dashboard overview
│   ├── optumgx/            # FEM simulation
│   ├── groundhog/          # Soil investigation
│   ├── gempy/              # 3D geological modeling
│   ├── pyoma2/             # Operational modal analysis
│   ├── iframe/             # 3D viewer
│   ├── openseespy/         # Structural analysis (stub)
│   ├── preprocessing/      # Data preprocessing (stub)
│   └── tracker/            # Tracking module (stub)
├── Data/                   # Data files
├── assets/                 # Static assets
└── requirements.txt        # Python dependencies
```

## Core Components

### 1. Main Application (app.py)

**Purpose**: Initializes the Dash application, sets up authentication, and manages global state.

**Key Features**:
- Basic authentication using environment variables
- Global data store for sharing state between pages
- Theme switching (light/dark mode)
- Auto-loading sensor data at 60-second intervals
- Error modal for centralized error handling
- Bootstrap styling with responsive design

**Key Callbacks**:
- `toggle_navbar_collapse`: Toggles mobile navigation
- `switch_theme`: Switches between light and dark themes
- `show_error`: Displays error messages from global store
- `auto_load_data`: Periodically loads sensor and soil data

### 2. Common Utilities (common/)

#### constants.py
Defines `PROJECT_DIR` as the base directory for the project.

#### navbar.py
Creates the navigation bar with:
- Brand name
- Theme switcher
- Dropdown menus for FEM and Data analysis tools
- Responsive mobile menu

#### utils.py

**Data Loading Functions**:
- `load_sensor_data_sync()`: Loads sensor data from NetCDF files with caching
- `load_soil_data_sync()`: Loads soil data from CSV files with caching
- `init_data()`: Initializes sample data if files don't exist

**Simulation Functions**:
- `simulate_optumgx()`: Simulates stress-strain curves for FEM analysis
- `simulate_pyoma2()`: Simulates frequency spectrum using FFT

**File Processing Functions**:
- `process_uploaded_file()`: Handles CSV/Excel uploads
- `process_vtk_file()`: Handles VTK file uploads

**Visualization Functions**:
- `create_bullet_chart()`: Creates performance indicator charts
- `create_gauge_chart()`: Creates gauge charts for monitoring
- `matplotlib_to_base64()`: Converts matplotlib figures to base64 images

### 3. Page Modules

Each page follows a consistent pattern:
- `__init__.py`: Registers the page with Dash
- `layout.py`: Defines the page layout
- `callbacks.py`: Implements page-specific callbacks

#### Home Page (pages/home/)
- Integrated dashboard with overview metrics
- Interactive map using Leaflet
- 3D soil visualization on map click
- Processing pipeline that chains all analysis tools
- Comparison of simulated vs. real sensor data

#### OptumGX Page (pages/optumgx/)
- File upload for soil profile data
- Editable data table with missing value fixing
- Material strength parameter input
- Stress-strain curve visualization
- Export to PNG/PDF using clientside callbacks
- Download results as CSV

#### Groundhog Page (pages/groundhog/)
- Dual file upload (CPT data and layering)
- Data validation and visualization
- CPT processing using groundhog library
- Soil profile analysis
- Correlation calculations (e.g., relative density)
- Plot generation with matplotlib

#### PyOMA2 Page (pages/pyoma2/)
- Sensor data upload
- Operational modal analysis
- Frequency spectrum visualization
- Optional: Real PyOMA2 integration (falls back to simulation)

#### GemPy Page (pages/gempy/)
- 3D geological modeling
- Surface points and orientations input
- Model computation and visualization

#### IFrame Page (pages/iframe/)
- 3D viewer integration
- VTK file support

## Data Flow

### Global State Management

The application uses `dcc.Store` (id='global-store') to share data between pages:

```python
{
    'soil': [...],                    # Soil data records
    'sensor': {...},                  # Sensor xarray dataset
    'optumgx_data': [...],           # Uploaded OptumGX data
    'optumgx_result': [...],         # Simulation results
    'groundhog_cpt': [...],          # CPT data
    'groundhog_layering': [...],     # Soil layering
    'groundhog_cpt_processed': [...], # Processed CPT data
    'gempy_surfaces': [...],         # GemPy surface points
    'gempy_orientations': [...],     # GemPy orientations
    'pyoma2_data': [...],            # PyOMA2 input data
    'pyoma2_result': {...},          # Frequency analysis results
    'error': '...'                   # Error messages
}
```

### Processing Pipeline

The home page implements a sequential processing pipeline:
1. OptumGX: FEM simulation
2. Groundhog: CPT processing and soil profile analysis
3. GemPy: 3D geological model computation
4. PyOMA2: Modal analysis

Each step stores results in the global store for downstream use.

## Technical Stack

### Core Libraries
- **Dash**: Web application framework
- **Plotly**: Interactive visualizations
- **Dash Bootstrap Components**: UI components
- **Pandas/NumPy**: Data manipulation
- **Xarray**: Multi-dimensional sensor data

### Domain-Specific Libraries
- **OptumGX**: FEM analysis (simulated)
- **Groundhog**: Geotechnical analysis
- **GemPy**: 3D geological modeling
- **PyOMA2**: Operational modal analysis
- **PyVista**: 3D visualization

### Additional Components
- **Dash Leaflet**: Interactive maps
- **Dash IconFY**: Icon support
- **Dash DAQ**: Dashboard components

## Security

- Basic authentication with credentials from environment variables
- Default credentials: admin/secret (should be changed via env vars)
- Uses `DASH_USERNAME` and `DASH_PASSWORD` environment variables

## Asynchronous Operations

The application uses async/await for:
- Auto-loading data at intervals
- Processing pipeline execution
- File I/O operations

Thread pool executors handle blocking operations in async contexts.

## Error Handling

- Centralized error handling through global store
- Error modal displays issues to users
- Comprehensive logging throughout the application
- Try-catch blocks in all callbacks

## Performance Optimizations

- LRU caching for data loading functions (`@functools.lru_cache`)
- Clientside callbacks for export operations
- Lazy loading of page modules
- Periodic data refresh (60 seconds)

## Detailed Improvement Recommendations

### Critical Priority (Security & Stability)

1. **Authentication & Security** (app.py:45-51)
   - Replace BasicAuth with JWT-based authentication
   - Add session management with timeout
   - Implement rate limiting to prevent brute force attacks
   - Consider OAuth2 integration for enterprise deployment
   - Add CSRF protection for all forms

2. **Input Validation** (common/utils.py:87-103)
   - Add file size limits (currently unlimited, memory risk)
   - Implement virus/malware scanning for uploads
   - Add schema validation for uploaded data
   - Validate file content beyond extension checking
   - Add proper encoding detection for CSV files

3. **Error Handling** (app.py:118-130)
   - Add comprehensive try-catch blocks in auto_load_data
   - Implement retry logic with exponential backoff
   - Add circuit breaker pattern for external services
   - Create custom exception classes for better error tracking
   - Add error monitoring/alerting system

4. **Data Validation** (common/utils.py:22-54)
   - Add coordinate bounds validation for soil data
   - Implement timestamp verification for sensor data
   - Add data quality checks (outliers, missing values)
   - Validate physical constraints (e.g., qc > 0)
   - Add metadata validation

### High Priority (Performance & Scalability)

5. **Database Integration**
   - Replace file-based storage with PostgreSQL/TimescaleDB
   - Implement connection pooling
   - Add database migrations (Alembic)
   - Use PostGIS for spatial data
   - Implement proper indexing strategies

6. **Caching Strategy** (common/utils.py:21, 40)
   - Replace simple LRU cache with Redis
   - Implement cache invalidation strategy
   - Add cache warming for frequently accessed data
   - Configure appropriate TTL values
   - Monitor cache hit rates

7. **Asynchronous Operations**
   - Convert all file I/O to async operations
   - Use Dask for large dataset processing
   - Implement background job queue (Celery/RQ)
   - Add progress tracking for long operations
   - Optimize ThreadPoolExecutor usage

8. **Map Performance** (pages/home/callbacks.py:39-50)
   - Implement marker clustering for >100 markers
   - Use server-side rendering for large datasets
   - Add viewport-based data loading
   - Implement virtual scrolling for data tables
   - Optimize GeoJSON rendering

### Medium Priority (Features & UX)

9. **Data Loading** (common/utils.py)
   - Add support for real-time data sources (MQTT, WebSocket)
   - Implement incremental data loading
   - Add data export to multiple formats (GeoJSON, Parquet, HDF5)
   - Support streaming data ingestion
   - Add data versioning

10. **Visualization Enhancements** (pages/home/layout.py)
    - Add interactive filtering and searching
    - Implement custom marker icons by formation type
    - Add drawing tools for map annotations
    - Implement time-series animation
    - Add 3D terrain visualization

11. **Processing Pipeline** (pages/home/callbacks.py:82-154)
    - Add pipeline configuration UI
    - Implement step-by-step execution with pause/resume
    - Add pipeline versioning and history
    - Implement parallel execution where possible
    - Add pipeline validation before execution

12. **3D Visualization** (pages/home/callbacks.py:50-74)
    - Replace off_screen=True with interactive viewer
    - Add multiple view modes (orthographic, perspective)
    - Implement cross-sections and slicing
    - Add measurement tools
    - Support VR/AR viewing

### Low Priority (Code Quality & Maintenance)

13. **Type Hints**
    - Add type hints to all functions
    - Use mypy for static type checking
    - Add dataclasses for structured data
    - Use Pydantic for data validation
    - Create type stubs for external libraries

14. **Testing**
    - Add unit tests (pytest) - current coverage: 0%
    - Add integration tests for workflows
    - Add end-to-end tests (Selenium/Playwright)
    - Add performance benchmarks
    - Implement continuous testing in CI/CD

15. **Logging & Monitoring**
    - Implement structured logging (JSON format)
    - Add log rotation and archiving
    - Add application performance monitoring (APM)
    - Implement distributed tracing
    - Add custom metrics and dashboards

16. **Code Organization**
    - Extract configuration to separate files (config.py, .env)
    - Create separate modules for each analysis tool
    - Implement dependency injection
    - Add interfaces/protocols for extensibility
    - Refactor large callbacks into service classes

17. **Documentation**
    - Add docstrings to all functions (Google/NumPy style)
    - Create API documentation (Sphinx)
    - Add architecture diagrams
    - Create user manual
    - Add inline comments for complex logic

18. **Deployment**
    - Create Docker containerization
    - Add docker-compose for multi-service setup
    - Implement proper secrets management (Vault, AWS Secrets)
    - Add health check endpoints
    - Create Kubernetes manifests for orchestration

### File-Specific Recommendations

#### app.py
- Line 17: Add structured logging with file rotation
- Line 43-51: Upgrade authentication system
- Line 64: Make auto-refresh interval configurable
- Line 133: Add production deployment configuration
- Add middleware for request logging and timing

#### common/utils.py
- Lines 18-38: Add async versions of data loading functions
- Lines 82-89: Replace simulation with real OptumGX integration
- Lines 107-124: Add customization options for charts
- Add data validation utilities
- Create separate modules for each concern (io, visualization, simulation)

#### pages/home/callbacks.py
- Lines 82-154: Break pipeline into separate functions
- Lines 50-74: Improve 3D viewer performance
- Add unit tests for each callback
- Extract business logic from callbacks
- Add request debouncing for map interactions

#### common/navbar.py
- Add user profile menu
- Implement breadcrumbs
- Add search functionality
- Make navigation configurable
- Add keyboard shortcuts

### Technical Debt Items

1. **Temporary File Management** (pages/home/callbacks.py:111-130)
   - Ensure all temp files are cleaned up on error
   - Use context managers for temp file handling
   - Add periodic cleanup job

2. **Global State Management** (app.py:55)
   - Consider using dcc.Store with local storage
   - Implement state versioning
   - Add state persistence to database
   - Handle concurrent user sessions properly

3. **Import Organization**
   - Many pages have duplicate imports
   - Create common import groups
   - Use __all__ in __init__.py files
   - Remove unused imports

4. **Magic Numbers**
   - Extract hardcoded values to constants
   - Create configuration schema
   - Make parameters configurable via UI

5. **Error Messages**
   - Create user-friendly error messages
   - Add error codes for tracking
   - Implement i18n for multi-language support
   - Add contextual help for errors

### Performance Benchmarks to Track

- Page load time (target: <2s)
- Data loading time (target: <500ms for 10k records)
- Map rendering time (target: <1s for 1000 markers)
- 3D visualization generation (target: <3s)
- Pipeline execution time per step
- Memory usage per user session
- API response times

### Recommendations Summary by Module

| Module | Critical | High | Medium | Low | Total |
|--------|----------|------|--------|-----|-------|
| app.py | 2 | 1 | 2 | 3 | 8 |
| common/utils.py | 2 | 2 | 3 | 2 | 9 |
| pages/home/ | 1 | 2 | 4 | 2 | 9 |
| pages/optumgx/ | 1 | 1 | 2 | 1 | 5 |
| pages/groundhog/ | 0 | 1 | 2 | 1 | 4 |
| Infrastructure | 1 | 3 | 1 | 4 | 9 |
| **Total** | **7** | **10** | **14** | **13** | **44** |

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables for authentication
3. Run: `python app.py`
4. Access: http://localhost:8050

## Data Requirements

### Sensor Data (data/sensor_data.nc)
NetCDF format with:
- Dimensions: time, channel
- Variable: value
- Auto-generated if missing

### Soil Data (data/soil_data.csv)
CSV format with columns:
- x, y, z: coordinates
- formation: soil type
- qc: cone resistance
- fs: sleeve friction
- Auto-generated if missing

## Known Issues

1. PyOMA2 library may require special installation
2. Some pages are stubs (openseespy, preprocessing, tracker)
3. GemPy temporary file cleanup in pipeline
4. Missing error handling for file upload size limits
5. No validation for uploaded file formats beyond extension checking

## Future Development

1. Complete stub pages (OpenSeesPy, Preprocessing, Tracker)
2. Add user management and role-based access
3. Implement real-time data streaming
4. Add database backend for persistent storage
5. Enhance 3D visualization capabilities
6. Add export to multiple formats
7. Implement comprehensive unit tests
8. Add API endpoints for external integrations
9. Performance monitoring and analytics
10. Mobile-responsive improvements
