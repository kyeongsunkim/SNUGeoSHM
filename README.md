# SNUGeoSHM - Offshore Wind Turbine Monitoring Dashboard

A comprehensive web-based digital twin platform for monitoring offshore wind turbines, integrating geological analysis, structural modeling, and sensor data visualization.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Dash](https://img.shields.io/badge/Dash-2.0+-green.svg)](https://dash.plotly.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Features

- **Multi-Page Dashboard**: Modular architecture with dedicated pages for different analysis tools
- **Real-Time Monitoring**: Periodic data refresh with sensor data visualization
- **Geological Modeling**: Integration with GemPy for 3D geological visualization
- **Structural Analysis**: FEM simulation with OptumGX integration
- **Geotechnical Analysis**: CPT processing and soil profile analysis via Groundhog
- **Modal Analysis**: Operational modal analysis using PyOMA2
- **Interactive Mapping**: Leaflet-based maps with soil data points
- **3D Visualization**: PyVista integration for 3D soil visualization
- **Data Validation**: Comprehensive input validation and error handling
- **Secure Authentication**: User authentication with configurable credentials
- **Docker Support**: Containerized deployment with docker-compose

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/SNUGeoSHM.git
cd SNUGeoSHM

# Copy environment configuration
cp .env.example .env

# Edit .env with your settings
nano .env

# Start with docker-compose
docker-compose up -d

# Access the application
open http://localhost:8050
```

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Run the application
python app.py
```

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- (Optional) Docker and docker-compose for containerized deployment
- (Optional) PostgreSQL 15+ with PostGIS for database backend
- (Optional) Redis for caching

### System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    gcc \
    g++ \
    gfortran \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev
```

#### macOS
```bash
brew install geos proj spatialindex
```

#### Windows
Most dependencies are included in Python wheels. For spatial libraries:
```bash
# Install from conda-forge (recommended)
conda install -c conda-forge geos proj
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

Core dependencies include:
- `dash` - Web application framework
- `plotly` - Interactive visualizations
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `xarray` - Multi-dimensional data handling
- `gempy` - 3D geological modeling
- `groundhog` - Geotechnical analysis
- `pyvista` - 3D visualization
- `dash-leaflet` - Interactive maps

## Configuration

### Environment Variables

Configuration is managed through environment variables. Copy `.env.example` to `.env` and modify:

```bash
# Security
SECRET_KEY=your-secret-key-here
DASH_USERNAME=admin
DASH_PASSWORD=your-secure-password

# Database (optional - defaults to file-based storage)
DB_TYPE=postgres  # or 'file'
DB_HOST=localhost
DB_PORT=5432
DB_NAME=snugeoshm
DB_USER=postgres
DB_PASSWORD=your-db-password

# Cache (optional - defaults to simple in-memory cache)
CACHE_TYPE=redis  # or 'simple'
REDIS_HOST=localhost
REDIS_PORT=6379

# Application
DEBUG=False
PORT=8050
LOG_LEVEL=INFO
DATA_REFRESH_INTERVAL_MS=60000
```

### Configuration File

Advanced configuration can be done through `config.py`:

```python
from config import config

# Access configuration
print(config.app.DEBUG)
print(config.data.DATA_DIR)
print(config.security.SESSION_TIMEOUT_MINUTES)
```

## Usage

### Starting the Application

#### Development Mode
```bash
python app.py
```

#### Production Mode
```bash
# Set environment variables
export DEBUG=False
export SECRET_KEY=your-production-secret

# Run with gunicorn
gunicorn app:server -b 0.0.0.0:8050 -w 4
```

### Accessing the Dashboard

Open your browser and navigate to:
- Local: `http://localhost:8050`
- Network: `http://your-ip:8050`

Default credentials (change in production):
- Username: `admin`
- Password: `secret`

### Data Requirements

#### Sensor Data (`data/sensor_data.nc`)
NetCDF format with dimensions:
- `time`: Timestamp dimension
- `channel`: Sensor channel dimension

Variables:
- `value`: Sensor readings (2D array: time × channel)

#### Soil Data (`data/soil_data.csv`)
CSV format with columns:
- `x`, `y`, `z`: Coordinates (m)
- `formation`: Soil type (string)
- `qc`: Cone resistance (MPa)
- `fs`: Sleeve friction (MPa)

Sample data is automatically generated if files don't exist.

## Architecture

### Project Structure

```
SNUGeoSHM/
├── app.py                 # Main application entry point
├── config.py              # Configuration management
├── common/                # Shared utilities
│   ├── constants.py       # Global constants
│   ├── navbar.py          # Navigation component
│   ├── utils_improved.py  # Enhanced utilities
│   ├── validation.py      # Data validation
│   ├── error_handling.py  # Error handling & retry logic
│   └── logging_config.py  # Logging configuration
├── pages/                 # Page modules
│   ├── home/              # Dashboard overview
│   ├── optumgx/           # FEM simulation
│   ├── groundhog/         # Geotechnical analysis
│   ├── gempy/             # Geological modeling
│   ├── pyoma2/            # Modal analysis
│   └── ...                # Other pages
├── data/                  # Data files
├── assets/                # Static assets (CSS, images)
├── tests/                 # Unit tests
├── logs/                  # Application logs
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Multi-container setup
└── requirements.txt       # Python dependencies
```

### Technology Stack

**Frontend:**
- Dash & Plotly for interactive dashboards
- Dash Bootstrap Components for UI
- Dash Leaflet for maps
- Dash IconiFY for icons

**Backend:**
- Python 3.11+
- Pandas & NumPy for data processing
- Xarray for multidimensional data
- Flask (via Dash) for web server

**Analysis Tools:**
- GemPy for geological modeling
- Groundhog for geotechnical analysis
- PyVista for 3D visualization
- PyOMA2 for modal analysis

**Infrastructure:**
- Docker for containerization
- PostgreSQL + PostGIS for database (optional)
- Redis for caching (optional)
- Nginx for reverse proxy (optional)

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/SNUGeoSHM.git
cd SNUGeoSHM

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Install pre-commit hooks
pre-commit install

# Run in debug mode
export DEBUG=True
python app.py
```

### Code Style

We follow PEP 8 style guidelines:
```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy common/ pages/
```

### Adding New Pages

1. Create page directory: `pages/yourpage/`
2. Create `__init__.py` to register page:
```python
import dash
from .layout import layout

dash.register_page(__name__, path='/yourpage', layout=layout)
```
3. Create `layout.py` with page layout
4. Create `callbacks.py` with page logic

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=common --cov=pages

# Run specific test file
pytest tests/test_validation.py

# Run with verbose output
pytest -v
```

### Writing Tests

Tests are located in the `tests/` directory:
- `test_validation.py` - Data validation tests
- `test_utils.py` - Utility function tests
- `test_app.py` - Application integration tests

Example test:
```python
import pytest
from common.validation import validate_soil_data

def test_soil_validation():
    df = create_sample_soil_data()
    result = validate_soil_data(df)
    assert result is not None
```

## Deployment

### Docker Deployment

#### Single Container
```bash
# Build image
docker build -t snugeoshm:latest .

# Run container
docker run -d \
  --name snugeoshm \
  -p 8050:8050 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=your-secret \
  snugeoshm:latest
```

#### Multi-Container with docker-compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Production Deployment

#### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn app:server \
  --bind 0.0.0.0:8050 \
  --workers 4 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

#### Using Systemd Service

Create `/etc/systemd/system/snugeoshm.service`:
```ini
[Unit]
Description=SNUGeoSHM Dashboard
After=network.target

[Service]
Type=notify
User=appuser
WorkingDirectory=/opt/snugeoshm
Environment="PATH=/opt/snugeoshm/.venv/bin"
ExecStart=/opt/snugeoshm/.venv/bin/gunicorn app:server -c gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable snugeoshm
sudo systemctl start snugeoshm
sudo systemctl status snugeoshm
```

### Nginx Reverse Proxy

Configure Nginx (`/etc/nginx/sites-available/snugeoshm`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment-Specific Configuration

#### Development
```bash
DEBUG=True
LOG_LEVEL=DEBUG
DATA_REFRESH_INTERVAL_MS=5000
```

#### Staging
```bash
DEBUG=False
LOG_LEVEL=INFO
ENABLE_METRICS=True
```

#### Production
```bash
DEBUG=False
LOG_LEVEL=WARNING
SECRET_KEY=complex-random-key
DB_TYPE=postgres
CACHE_TYPE=redis
ENABLE_METRICS=True
SENTRY_DSN=your-sentry-dsn
```

## Performance Optimization

### Caching

Enable Redis caching:
```bash
CACHE_TYPE=redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Database

Use PostgreSQL for better performance:
```bash
DB_TYPE=postgres
DB_HOST=localhost
DB_NAME=snugeoshm
```

### Application

- Adjust worker count based on CPU cores
- Enable compression for large datasets
- Use CDN for static assets in production

## Monitoring

### Logs

Logs are written to `logs/` directory:
- `app.log` - All application logs
- `errors.log` - Error logs only
- `app.json` - Structured JSON logs (production)

### Health Checks

Health endpoint: `http://localhost:8050/_dash-layout`

### Metrics

Enable metrics collection:
```bash
ENABLE_METRICS=True
METRICS_PORT=9090
```

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Permission Errors:**
```bash
# Fix directory permissions
chmod -R 755 data/ logs/ outputs/
```

**Port Already in Use:**
```bash
# Change port in .env
PORT=8051

# Or kill existing process
lsof -i :8050
kill -9 <PID>
```

**Database Connection Errors:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d snugeoshm
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Review

All submissions require review. We use GitHub pull requests for this purpose.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- GemPy team for geological modeling capabilities
- Groundhog contributors for geotechnical analysis tools
- Dash/Plotly team for the excellent framework
- All open-source contributors

## Contact

- Project Lead: [Your Name](mailto:your.email@example.com)
- Project Link: [https://github.com/yourusername/SNUGeoSHM](https://github.com/yourusername/SNUGeoSHM)
- Documentation: [https://snugeoshm.readthedocs.io](https://snugeoshm.readthedocs.io)

## Recent Bug Fixes (2025-12-01)

All critical bugs have been identified and fixed across three modules:

### Groundhog (6 bugs fixed)
- ✅ Missing u2_key parameter
- ✅ Premature normalization issue
- ✅ Wrong SoilProfile structure handling
- ✅ Non-existent method calls removed
- ✅ Incorrect plot parameters fixed
- ✅ Missing correlation setup handled

### GemPy (3 bugs fixed)
- ✅ Solutions serialization failure (now stores metadata)
- ✅ Temp file cleanup vulnerability (try/finally added)
- ✅ Missing input validation (comprehensive checks added)

### PyOMA2 (2 bugs fixed)
- ✅ Empty result extraction (using FFT simulation fallback)
- ✅ Missing data validation (min sample checks added)

**Documentation**: See [FINAL_REPORT.md](FINAL_REPORT.md) for complete bug details and fixes.

**Testing**: 20+ pytest tests added in `tests/test_groundhog_integration.py`

## Roadmap

See [CLAUDE.md](CLAUDE.md) for detailed improvement recommendations and future enhancements.

### Upcoming Features

- [ ] Real-time data streaming via MQTT
- [ ] Machine learning-based anomaly detection
- [ ] Mobile-responsive design improvements
- [ ] API endpoints for external integrations
- [ ] Advanced user management with roles
- [ ] Export to multiple formats (PDF, Excel, HDF5)
- [ ] Automated reporting system
- [ ] Integration with cloud storage (AWS S3, Azure Blob)

## Citation

If you use this software in your research, please cite:

```bibtex
@software{snugeoshm2024,
  title={SNUGeoSHM: Offshore Wind Turbine Monitoring Dashboard},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/SNUGeoSHM}
}
```
