# Renewable Energy Output Forecaster 🌞💨⚡

A Django-based web application that predicts solar and wind energy generation using open weather data and machine learning. This platform helps energy providers, solar farm operators, and homeowners optimize their renewable energy usage without requiring physical sensors.

## 🌟 Features

### Core Functionality
- **Real-time Energy Forecasting**: Predict solar/wind power output for 24-72 hours ahead
- **Multiple Data Source Integration**: Aggregate data from various open weather APIs
- **Machine Learning Pipeline**: Automated model training and prediction
- **Interactive Dashboard**: Visualize forecasts, historical data, and performance metrics
- **RESTful API**: Programmatic access to forecasting data
- **Alert System**: Notifications for unusual generation patterns or forecast errors

### Advanced Capabilities
- **Uncertainty Quantification**: Prediction intervals (P10, P50, P90) for risk assessment
- **Anomaly Detection**: Identify underperforming systems or data quality issues
- **Multi-location Support**: Manage forecasts for multiple sites simultaneously
- **Seasonal Analysis**: Long-term trend analysis and seasonal pattern recognition
- **Export Functionality**: Download forecasts and reports in multiple formats

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Django Backend  │───▶│  Frontend       │
│                 │    │                  │    │                 │
│ • OpenWeather   │    │ • Data Ingestion │    │ • Dashboard     │
│ • NASA POWER    │    │ • ML Pipeline    │    │ • Analytics     │
│ • NOAA          │    │ • API Endpoints  │    │ • User Mgmt     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Data Storage   │
                    │                  │
                    │ • PostgreSQL     │
                    │ • InfluxDB       │
                    │ • Redis          │
                    └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/renewable-energy-forecaster.git
cd renewable-energy-forecaster
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database setup**
```bash
python manage.py migrate
python manage.py create_initial_locations
```

6. **Start the development server**
```bash
python manage.py runserver
```

## ⚙️ Configuration

### Environment Variables

```ini
# Database
DATABASE_URL=postgres://user:password@localhost:5432/energy_forecaster

# Cache
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENWEATHER_API_KEY=your_api_key_here
NASA_POWER_USERNAME=your_username
NASA_POWER_PASSWORD=your_password

# Django Settings
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Data Source Configuration

Edit `config/data_sources.yaml` to configure your data sources:

```yaml
openweather:
  api_key: "your_api_key"
  update_frequency: 3600  # seconds

nasa_power:
  parameters:
    - ALLSKY_SFC_SW_DWN  # Solar radiation
    - T2M                # Temperature
    - WS2M               # Wind speed
```

## 📊 Project Structure

```
energy_forecaster/
├── apps/
│   ├── data_collection/     # Data ingestion from APIs
│   ├── ml_pipeline/         # Machine learning models
│   ├── dashboard/           # Frontend views and templates
│   ├── api/                 # REST API endpoints
│   └── alerts/              # Notification system
├── config/                  # Configuration files
├── static/                  # CSS, JS, images
├── media/                   # User uploads and exports
├── tests/                   # Test suites
└── manage.py
```

## 🔧 Usage

### Basic Forecasting

1. **Add a Location**
   - Navigate to the dashboard
   - Click "Add Location"
   - Enter coordinates or address
   - Specify energy system parameters (solar panel capacity, wind turbine specs)

2. **View Forecasts**
   - Access the main dashboard for overview
   - Drill down to location-specific details
   - Compare forecast vs actual performance

3. **Generate Reports**
   - Export forecasts as CSV, PDF, or Excel
   - Schedule automated report generation
   - Access via API for integration with other systems

### API Usage

```python
import requests

# Get forecast for a location
response = requests.get(
    "http://localhost:8000/api/forecast/location/1/",
    headers={"Authorization": "Token your_api_token"}
)

# Historical data
response = requests.get(
    "http://localhost:8000/api/historical/location/1/?days=30"
)
```

## 🤖 Machine Learning Models

### Current Models

1. **Solar Forecasting**
   - Gradient Boosting Regressor (primary)
   - Random Forest (fallback)
   - Physical model (clear-sky baseline)

2. **Wind Forecasting**
   - Power curve modeling
   - Temporal pattern recognition
   - Directional effects consideration

### Model Training

```bash
# Train solar models
python manage.py train_models --model-type solar --location all

# Evaluate model performance
python manage.py evaluate_models --days 30

# Generate feature importance report
python manage.py feature_importance --output report.html
```

## 📈 Data Sources

| Source | Data Type | Frequency | Cost | Usage |
|--------|-----------|-----------|------|-------|
| OpenWeatherMap | Forecasts | 3-hourly | Freemium | Primary forecasting |
| NASA POWER | Historical | Daily | Free | Model training |
| NOAA | Historical | Hourly | Free | Validation |
| Open-Meteo | Backup | Hourly | Free | Fallback source |

## 🧪 Testing

Run the test suite to ensure everything works correctly:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.ml_pipeline

# Generate test coverage report
coverage run manage.py test
coverage report
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run management commands
docker-compose exec web python manage.py migrate
```

### Production Deployment

1. **Set up reverse proxy (nginx)**
2. **Configure SSL certificates**
3. **Set up database backups**
4. **Configure monitoring and alerts**

## 🔍 Monitoring & Analytics

The application includes built-in monitoring:

- **Performance metrics** via Django Debug Toolbar
- **Error tracking** with Sentry integration
- **API usage analytics**
- **Model performance tracking**

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Roadmap

### Phase 1 (Current)
- [x] Basic solar forecasting
- [x] Dashboard interface
- [x] API endpoints
- [x] Historical data integration

### Phase 2 (Next)
- [ ] Wind energy forecasting
- [ ] Advanced uncertainty modeling
- [ ] Mobile application
- [ ] Third-party integrations

### Phase 3 (Future)
- [ ] Hybrid system optimization
- [ ] Energy trading recommendations
- [ ] Climate change impact analysis

## 🐛 Troubleshooting

### Common Issues

**Data ingestion failures:**
```bash
# Check API connectivity
python manage.py test_api_connectivity

# Reset failed data collections
python manage.py reset_failed_jobs
```

**Model performance degradation:**
```bash
# Retrain models with recent data
python manage.py retrain_models --days 60

# Compare model versions
python manage.py model_comparison
```

### Getting Help

- Check the [FAQ](docs/FAQ.md)
- Open an [issue](https://github.com/yourusername/renewable-energy-forecaster/issues)
- Contact the development team

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Weather data providers: OpenWeatherMap, NASA, NOAA
- Machine learning libraries: scikit-learn, XGBoost
- Visualization libraries: Chart.js, D3.js
- Django community for excellent documentation and packages

## 📞 Contact

- Project Lead: [Your Name](mailto:your.email@example.com)
- Issues: [GitHub Issues](https://github.com/yourusername/renewable-energy-forecaster/issues)
- Documentation: [Project Wiki](https://github.com/yourusername/renewable-energy-forecaster/wiki)

---

**Note**: This is a development version. For production use, ensure proper security configuration and data validation.

*Built with ❤️ using Django and modern web technologies*
