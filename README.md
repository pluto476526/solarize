# Solarize - Solar Energy Analysis Platform

![Django](https://img.shields.io/badge/Django-4.2-green)
![PostgreSQL](https://img.shields.io/badge/TimescaleDB-Supported-blue)
![Plotly](https://img.shields.io/badge/Plotly-Charts-orange)
![Machine Learning](https://img.shields.io/badge/ML-LightGBM-yellow)

Solarize is a comprehensive Django web application for solar energy production analysis, prediction, and optimization. It combines physical solar modeling with machine learning to provide accurate energy production forecasts and financial analysis.

## 🌟 Features

### Core Functionality
- **Solar Production Simulation**: PVWatts-based energy production modeling
- **Machine Learning Enhancement**: LightGBM-based environmental pattern learning
- **Multi-location Support**: Compare solar potential across different sites
- **Financial Analysis**: ROI, payback period, and savings calculations
- **Environmental Impact**: Carbon offset and environmental benefit tracking
- **Interactive Visualizations**: Plotly-powered charts and dashboards

### Advanced Capabilities
- **Real-time Weather Integration**: Environmental data-driven predictions
- **Scenario Analysis**: Compare different system configurations
- **Time-series Data Storage**: TimescaleDB for efficient time-series data
- **Pattern Recognition**: Machine learning enhanced production forecasts
- **Comprehensive Reporting**: Detailed analysis and recommendations

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 4.2+
- **Database**: TimescaleDB (PostgreSQL extension)
- **Machine Learning**: LightGBM, scikit-learn
- **Visualization**: Plotly Python, Chart.js
- **Frontend**: Bootstrap 5, JavaScript
- **Solar Calculations**: PVLib Python

### Data Flow
1. **Input Processing**: User parameters + location data
2. **Solar Simulation**: PVWatts physical modeling
3. **Feature Engineering**: Environmental and temporal features
4. **ML Prediction**: LightGBM pattern enhancement
5. **Analysis & Visualization**: Comparative results and insights

## 📊 Machine Learning Methodology

### Approach
Solarize uses a hybrid approach that enhances traditional PVWatts simulations with machine learning:

```python
# Core Philosophy: Enhance, Don't Replace
PVWatts (Physical Model) + LightGBM (Environmental Patterns) = Enhanced Predictions
```

### Feature Engineering
- **Astronomical Features**: Sun elevation, azimuth, solar position
- **Temporal Features**: Hour, day of year, month, seasonal patterns
- **Environmental Features**: Temperature, humidity, cloud cover, wind speed
- **Interaction Features**: Temperature × sun elevation, cloud cover × sun elevation

### Model Architecture
```python
model = LGBMRegressor(
    n_estimators=300,
    learning_rate=0.05,
    num_leaves=63,
    random_state=42,
    max_depth=-1,
    min_child_samples=20
)
```

## 🚀 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+ with TimescaleDB extension
- Redis (for caching, optional)

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/solarize.git
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
python manage.py createcachetable
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

## 📈 Usage

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
- **Production Forecasts**: Energy generation predictions
- **Financial Analysis**: ROI and payback calculations
- **Environmental Impact**: Carbon offset metrics
- **Scenario Comparison**: Different configurations

## 🗄️ Database Schema

### TimescaleDB Hypertables
Solarize uses TimescaleDB hypertables for efficient time-series data storage:

```sql
-- Example hypertable for production data
SELECT create_hypertable('solar_production_data', 'timestamp');
```

### Key Models
- `Location`: Geographic and system parameters
- `SolarProduction`: Time-series energy data
- `WeatherData`: Environmental conditions
- `MLModel`: Trained machine learning models
- `AnalysisReport`: Generated reports and insights

## 🔧 Configuration

### Environment Variables
```ini
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:pass@localhost/solarize
ALLOWED_HOSTS=localhost,127.0.0.1
TIME_ZONE=UTC
```

### Django Settings
Key configuration in `settings.py`:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'solarize',  # main app
    'django_plotly_dash',  # for Plotly integration
    'bootstrap5',  # frontend framework
]

# TimescaleDB configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'solarize',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📊 API Endpoints

### REST API
- `GET /api/locations/` - List all locations
- `POST /api/analysis/` - Create new analysis
- `GET /api/reports/<id>/` - Get analysis report
- `GET /api/production-data/` - Time-series production data

### Data Export
- CSV export of production data
- PDF report generation
- JSON API for integration

## 🤖 Machine Learning Integration

### Training Process
1. **Data Collection**: Historical production + environmental data
2. **Feature Engineering**: Create ML-ready features
3. **Model Training**: LightGBM with cross-validation
4. **Validation**: Pattern correlation and physical plausibility checks
5. **Deployment**: Model persistence and inference

### Prediction Methods
- **PVWatts Only**: Standard physical simulation
- **Environment-Based**: Pure ML prediction
- **Hybrid Approach**: Average of both methods
- **Pattern Analysis**: Comparative insights

## 📈 Visualization

### Plotly Dashboards
- **Production Charts**: Hourly, daily, monthly views
- **Comparative Analysis**: Multiple scenarios
- **Financial Metrics**: ROI, savings, payback
- **Environmental Impact**: Carbon offset visualization

### Interactive Features
- **Zoom and Pan**: Detailed data exploration
- **Data Export**: Chart data download
- **Real-time Updates**: Live data integration
- **Responsive Design**: Mobile-friendly interfaces

## 🔍 Monitoring & Analytics

### Performance Metrics
- **Model Accuracy**: Pattern correlation scores
- **Data Quality**: Environmental data validation
- **System Health**: Database and application monitoring
- **User Analytics**: Usage patterns and preferences

### Logging
```python
import logging
logger = logging.getLogger('solarize')

# Usage examples
logger.info("Analysis completed", extra={'location_id': location.id})
logger.warning("Weather data unavailable", extra={'date': date})
```

## 🚀 Deployment

### Production Setup
1. **Web Server**: Gunicorn + Nginx
2. **Database**: TimescaleDB with connection pooling
3. **Caching**: Redis for session storage
4. **Static Files**: CDN or dedicated storage
5. **SSL**: HTTPS encryption

### Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "solarize.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Environment-Specific Settings
- **Development**: Debug mode, local database
- **Staging**: Production-like with test data
- **Production**: Optimized, secure configuration

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Code Style
```bash
# Format code
black solarize/
isort solarize/

# Type checking
mypy solarize/

# Testing
pytest
```

### Testing
```bash
# Run tests
python manage.py test

# Coverage report
coverage run manage.py test
coverage report
```

## 📚 Documentation

### Additional Resources
- [API Documentation](docs/api.md)
- [Database Schema](docs/database.md)
- [ML Methodology](docs/ml-methodology.md)
- [Deployment Guide](docs/deployment.md)

### Key Concepts
- **PVWatts**: NREL's photovoltaic energy production model
- **TimescaleDB**: Time-series optimized PostgreSQL
- **LightGBM**: Microsoft's gradient boosting framework
- **PVLib**: Python library for photovoltaic system modeling

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🙏 Acknowledgments

- **NREL**: For PVWatts API and solar modeling algorithms
- **TimescaleDB**: For time-series database technology
- **Plotly**: For interactive visualization library
- **LightGBM**: For machine learning framework

## 📞 Support

For support and questions:
- **Documentation**: Check the docs folder
- **Issues**: GitHub Issues page
- **Email**: support@solarize.example.com

## 🗺️ Roadmap

### Upcoming Features
- [ ] Real-time monitoring integration
- [ ] Advanced battery storage modeling
- [ ] Multi-currency financial analysis
- [ ] Mobile application
- [ ] API rate limiting and authentication
- [ ] Advanced ML model explainability

### Research & Development
- [ ] Transfer learning for new locations
- [ ] Ensemble modeling techniques
- [ ] Anomaly detection for system monitoring
- [ ] Climate change impact projections

---

<div align="center">
  
**Solarize** - Harnessing the power of the sun with data intelligence ☀️📊

</div>
