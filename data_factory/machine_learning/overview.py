import pandas as pd
import numpy as np
from lightgbm import LGBMRegressor
import pvlib
from sklearn.metrics import mean_absolute_error

# --- 1. Load and merge data (same as before) ---
pvwatts = pd.read_csv("pvwatts.csv", parse_dates=["timestamp"])
pvwatts.set_index("timestamp", inplace=True)

env = pd.read_csv("environment.csv", parse_dates=["timestamp"])
env.set_index("timestamp", inplace=True)

data = pvwatts.join(env, how="inner")

# --- 2. Enhanced feature engineering ---
latitude, longitude = 40.0, -105.0
solar_position = pvlib.solarposition.get_solarposition(
    time=data.index, latitude=latitude, longitude=longitude
)
data["sun_elevation"] = solar_position["elevation"]
data["sun_azimuth"] = solar_position["azimuth"]

# More comprehensive time features
data["hour"] = data.index.hour
data["dayofyear"] = data.index.dayofyear
data["month"] = data.index.month
data["dayofweek"] = data.index.dayofweek
data["is_weekend"] = data.index.dayofweek >= 5

# Weather interaction features
data["temp_effect"] = data["temp"] * data["sun_elevation"].clip(
    0
)  # Temp matters more when sun is high
data["cloud_sun_interaction"] = data["cloud_cover"] * data["sun_elevation"].clip(0)

# --- 3. Frame as pattern enhancement ---
# Use PVWatts as baseline, learn how environmental factors modulate it
features = [
    "temp",
    "humidity",
    "cloud_cover",
    "wind_speed",
    "sun_elevation",
    "sun_azimuth",
    "hour",
    "dayofyear",
    "month",
    "temp_effect",
    "cloud_sun_interaction",
]

X = data[features]
y = data[
    "ac_energy"
]  # Direct target - learn to predict PVWatts output from env factors

# --- 4. Time-aware split ---
split_idx = int(len(data) * 0.8)
X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

# --- 5. Train model to predict energy from environment ---
model = LGBMRegressor(
    n_estimators=300, learning_rate=0.05, num_leaves=63, random_state=42
)
model.fit(X_train, y_train)

# --- 6. Compare approaches ---
# Baseline: raw PVWatts
baseline_pred = data["ac_energy"].iloc[split_idx:]

# Model: environment-based prediction
env_based_pred = model.predict(X_val)

# Simple hybrid: average of both approaches
hybrid_pred = (baseline_pred.values + env_based_pred) / 2

print("Comparison of approaches:")
print(f"Raw PVWatts range: [{baseline_pred.min():.2f}, {baseline_pred.max():.2f}]")
print(
    f"Environment-based range: [{env_based_pred.min():.2f}, {env_based_pred.max():.2f}]"
)
