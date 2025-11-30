# Quick Start Guide - SNUGeoSHM

Get up and running with SNUGeoSHM in 5 minutes!

## Prerequisites

- Python 3.11+ installed
- Git installed (optional)
- Docker installed (for containerized deployment)

## Option 1: Docker (Easiest - Recommended)

```bash
# 1. Navigate to project directory
cd SNUGeoSHM

# 2. Copy and configure environment
cp .env.example .env

# 3. Edit .env with your credentials (IMPORTANT!)
# At minimum, change:
#   SECRET_KEY=your-random-secret-key-here
#   DASH_PASSWORD=your-secure-password-here

# 4. Start the application
docker-compose up -d

# 5. Access the dashboard
# Open browser: http://localhost:8050
# Login: admin / (your password from .env)
```

That's it! The application is running with all services.

## Option 2: Local Development

```bash
# 1. Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env file with your settings

# 4. Run the application
python app.py

# 5. Access the dashboard
# Open browser: http://localhost:8050
# Login: admin / (your password from .env)
```

## First Time Setup

### 1. Change Default Credentials

Edit `.env`:
```bash
DASH_USERNAME=your_username
DASH_PASSWORD=strong_password_here
SECRET_KEY=random-string-at-least-32-characters
```

### 2. Prepare Your Data (Optional)

Sample data is automatically generated, but to use your own:

**Sensor Data** (`data/sensor_data.nc`):
- NetCDF format
- Dimensions: `time`, `channel`
- Variable: `value`

**Soil Data** (`data/soil_data.csv`):
```csv
x,y,z,formation,qc,fs
1.0,2.0,-10.0,Sand,5.0,0.5
...
```

### 3. Verify Installation

```bash
# Run tests
pytest

# Check logs
tail -f logs/app.log
```

## Common Tasks

### Start/Stop Application

**Docker:**
```bash
docker-compose up -d      # Start
docker-compose down       # Stop
docker-compose restart    # Restart
docker-compose logs -f    # View logs
```

**Local:**
```bash
python app.py             # Start
Ctrl+C                    # Stop
```

### View Logs

```bash
# Docker
docker-compose logs -f app

# Local
tail -f logs/app.log
tail -f logs/errors.log
```

### Update Application

```bash
# Docker
docker-compose down
docker-compose up -d --build

# Local
git pull
pip install -r requirements.txt --upgrade
python app.py
```

### Reset Data

```bash
# Backup first!
cp -r data data_backup

# Remove data files (will be regenerated)
rm data/sensor_data.nc
rm data/soil_data.csv

# Restart application
```

## Troubleshooting

### Port Already in Use

```bash
# Change port in .env
PORT=8051

# Or kill process using port
# Windows
netstat -ano | findstr :8050
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8050
kill -9 <PID>
```

### Permission Errors

```bash
# Docker
docker-compose down
sudo chown -R $USER:$USER data/ logs/ outputs/
docker-compose up -d

# Local
chmod -R 755 data/ logs/ outputs/
```

### Import Errors

```bash
pip install -r requirements.txt --force-reinstall
```

### Cannot Connect to Database (Docker)

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

## Configuration Cheat Sheet

### Environment Variables (.env)

```bash
# Essential
SECRET_KEY=change-this-random-key
DASH_USERNAME=admin
DASH_PASSWORD=change-this
PORT=8050
DEBUG=False

# Database (optional)
DB_TYPE=file              # or 'postgres'
DB_HOST=postgres
DB_NAME=snugeoshm
DB_USER=postgres
DB_PASSWORD=dbpassword

# Cache (optional)
CACHE_TYPE=simple         # or 'redis'
REDIS_HOST=redis

# Performance
MAX_WORKERS=4
DATA_REFRESH_INTERVAL_MS=60000
```

### File Locations

```
SNUGeoSHM/
├── data/              # Data files
├── logs/              # Application logs
├── outputs/           # Exported files
├── temp/              # Temporary files
└── assets/            # Generated visualizations
```

## Next Steps

1. **Explore the Dashboard**
   - Home: Overview and pipeline
   - OptumGX: FEM simulation
   - Groundhog: Geotechnical analysis
   - GemPy: Geological modeling
   - PyOMA2: Modal analysis

2. **Upload Your Data**
   - Use file upload buttons
   - Supported formats: CSV, XLSX, NetCDF, VTK

3. **Run Processing Pipeline**
   - Home page → "Run Processing Pipeline"
   - Chains all analysis tools

4. **Customize Configuration**
   - Edit `.env` for settings
   - Restart application to apply changes

5. **Read Full Documentation**
   - `README.md` - Complete guide
   - `claude.md` - Technical details
   - `IMPROVEMENTS_IMPLEMENTED.md` - What's new

## Production Deployment

For production deployment, see:
- `README.md` - Deployment section
- Use environment variables for all secrets
- Set `DEBUG=False`
- Use PostgreSQL and Redis
- Enable HTTPS with Nginx
- Set up monitoring and backups

## Getting Help

- **Documentation**: See `README.md` and `claude.md`
- **Issues**: Check logs in `logs/` directory
- **Support**: Contact your system administrator
- **Development**: See `README.md` Development section

## Resources

- GitHub Repository: (your-repo-url)
- Documentation: (your-docs-url)
- Issue Tracker: (your-issues-url)

---

**Happy Monitoring! 🌊🔧**
