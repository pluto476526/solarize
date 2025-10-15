# Solarize - Solar Energy Analysis Platform

![Django](https://img.shields.io/badge/Django-4.2-green)
![PostgreSQL](https://img.shields.io/badge/TimescaleDB-Supported-blue)
![Plotly](https://img.shields.io/badge/Plotly-Charts-orange)
![Machine Learning](https://img.shields.io/badge/ML-LightGBM-yellow)

Solarize is a comprehensive solar energy modeling platform that provides accurate energy production estimates using industry-standard modeling tools. The platform combines NREL PVWatts and PVlib to deliver reliable solar system performance analysis.

## Features


### Core Capabilities

- **PVWatts Modeling**: Industry-standard energy production estimates from NREL
- **PVlib Advanced Modeling**: Detailed photovoltaic system performance analysis
- **NASA Climate Modelling**: Long-term climate data for strategic planning
- **Real-time Weather Data**: Current conditions from OpenWeather API
- **Astronomical Calculations**: Precise sun positioning and solar geometry
- **Air Quality Analysis**: Environmental impact assessment via OpenMeteo
- **Interactive Visualizations**: Plotly-powered charts and dashboards
- **Comprehensive Reporting**: Detailed analysis and recommendations

## Architecture

### Technology Stack
- **Backend**: Django 4.2+
- **Database**: TimescaleDB (PostgreSQL extension)
- **Modelling**: NREL PVWatts, Python PVlib
- **Visualization**: Plotly Python
- **Frontend**: HTML, css, Bootstrap 5, JavaScript
- **Solar Calculations**: Python pvlib

### Data Flow
1. **Input Processing**: User parameters + location data
2. **Solar Simulation**: PVWatts physical modeling, pvlib modelling
5. **Analysis & Visualization**: Comparative results and insights


## Installation

### Prerequisites
- Python 3+
- PostgreSQL 12+ with TimescaleDB extension
- Redis
- Celery

### Step 1: Clone Repository
```bash
git clone https://github.com/pluto476526/solarize.git
cd solarize
```

### Step 2: Set Up Python Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Database Setup
```bash
# Install TimescaleDB
# Follow: https://docs.timescale.com/install/latest/

# Create database
sudo -u postgres psql
CREATE DATABASE solarize;
\c solarize
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

### Step 4: Configuration
```bash
cp .env.example .env
# Edit .env with your settings:
# DATABASE_URL, SECRET_KEY, DEBUG, etc.
```

### Step 5: Database Migrations
```bash
python manage.py migrate
```

### Step 6: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 7: Run Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## Usage

### 1. Location Setup
Add solar installation locations with:
- **Location Name**: Descriptive identifier
- **Coordinates**: Latitude and longitude
- **System Configuration**: Capacity, azimuth, tilt

### 2. System Configuration
Configure your solar system:
- **System Capacity**: Total rated power (kW)
- **Azimuth**: Panel direction (0°=North, 180°=South)
- **Tilt Angle**: Panel inclination (0°-90°)
- **Array Type**: Fixed roof, tracking, etc.
- **Module Type**: Standard, premium, thin film

### 3. Analysis Parameters
- **System Losses**: Efficiency losses (10-20%)
- **Timeframe**: Hourly or monthly analysis
- **Environmental Data**: Weather integration

### 4. Generating Reports
- **Production Modelling**: Energy generation estimates

### Data Export Formats
- CSV
- JSON


### Logging
```python
import logging
logger = logging.getLogger('solarize')

# Usage examples
logger.info("Analysis completed", extra={'location_id': location.id})
logger.warning("Weather data unavailable", extra={'date': date})
```

## Code Style
```bash
# Format code
black solarize/
isort solarize/

# Type checking
mypy solarize/

# Testing
pytest
```


## Key Concepts
- **PVWatts**: NREL's photovoltaic energy production model
- **PVLib**: Python library for photovoltaic system modeling
- **NASA POWER**: Data driven modelling

## License


## Support

For support and questions:
- **Email**: pkibuka@milky-way.space

## Roadmap

### Upcoming Features
- [ ] Real-time monitoring integration
- [ ] API

---

<div align="center">
  
**Solarize** - Harnessing the power of the sun with data intelligence

</div>
