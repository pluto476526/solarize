# --------------------------------------------------------------
#  NASA POWER + FAO-56 Crop Water Requirement Calculator (Plotly)
# --------------------------------------------------------------
import requests
import pandas as pd
import numpy as np
from scipy.stats import linregress
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
from typing import List, Dict, Optional, Tuple

warnings.filterwarnings("ignore")


class SolarAgriProjector:
    """
    NASA POWER + FAO-56 Crop Water Requirement (ET₀, CWR, Irrigation Need)
    Interactive Plotly visualisations.
    """

    BASE_URL = "https://power.larc.nasa.gov/api/projection/daily/point"

    PARAMETERS = {
        "solar_radiation": ("ALLSKY_SFC_SW_DWN", "kWh m⁻² day⁻¹"),
        "temperature": ("T2M", "°C"),
        "max_temp": ("T2M_MAX", "°C"),
        "min_temp": ("T2M_MIN", "°C"),
        "precipitation": ("PRECTOTCORR", "mm day⁻¹"),
        "relative_humidity": ("RH2M", "%"),
        "wind_speed": ("WS2M", "m s⁻¹"),
    }

    SCENARIOS = ["historical", "ssp245", "ssp585"]

    # Crop coefficients (Kc) – mid-season values (source: FAO-56)
    CROP_KC = {
        "maize": 1.15,
        "wheat": 1.15,
        "rice": 1.20,
        "tomato": 1.15,
        "soybean": 1.15,
        "potato": 1.15,
        "sugarcane": 1.25,
        "cotton": 1.15,
        "grass": 1.00,  # reference
    }

    def __init__(self, latitude: float, longitude: float):
        self.lat = latitude
        self.lon = longitude
        self.raw_data: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.insights: Dict[str, Dict[str, dict]] = {}
        self.et0: Dict[str, pd.DataFrame] = {}  # ET₀ per scenario
        self.cwr: Dict[str, pd.DataFrame] = {}  # Crop Water Requirement
        self.balance: Dict[str, pd.DataFrame] = {}  # Water balance

    # ------------------------------------------------------------------
    # 1. FETCH DATA
    # ------------------------------------------------------------------
    def _fetch_one(self, param_key: str, scenario: str) -> pd.DataFrame:
        code, _ = self.PARAMETERS[param_key]
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "community": "RE",
            "parameters": code,
            "format": "json",
            "start": "1981",
            "end": "2100" if scenario != "historical" else "2020",
            "temporal": "monthly",
        }
        if scenario != "historical":
            params["scenario"] = scenario.upper()

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=30)
            r.raise_for_status()
            payload = r.json()
            series = payload["properties"]["parameter"][code]
            df = pd.DataFrame.from_dict(series, orient="index", columns=[param_key])
            df.index = pd.to_datetime(df.index, format="%Y%m")
            df = df.astype(float).replace(-999, np.nan).dropna()
            return df
        except Exception as e:
            print(f"  [Failed] {param_key} ({scenario}): {e}")
            return pd.DataFrame()

    def fetch(self, parameters: List[str], scenarios: Optional[List[str]] = None):
        if scenarios is None:
            scenarios = self.SCENARIOS
        valid = [p for p in parameters if p in self.PARAMETERS]

        for scn in scenarios:
            self.raw_data[scn] = {}
            print(f"\nFetching {scn.upper()} ...")
            for p in valid:
                print(f"  • {p.replace('_', ' ').title()}", end="")
                df = self._fetch_one(p, scn)
                if not df.empty:
                    self.raw_data[scn][p] = df
                    print(" [Done]")
                else:
                    print(" [Skipped]")

    # ------------------------------------------------------------------
    # 2. FAO-56 PENMAN-MONTEITH ET₀
    # ------------------------------------------------------------------
    def compute_fao56_et0(self):
        """Compute Reference Evapotranspiration (ET₀) using FAO-56 PM equation."""
        required = ["max_temp", "min_temp", "solar_radiation", "relative_humidity", "wind_speed"]
        self.et0 = {}

        for scn in self.raw_data:
            if not all(p in self.raw_data[scn] for p in required):
                print(f"  [Skip ET₀] {scn}: missing data")
                continue

            df = pd.concat([
                self.raw_data[scn]["max_temp"],
                self.raw_data[scn]["min_temp"],
                self.raw_data[scn]["solar_radiation"],
                self.raw_data[scn]["relative_humidity"],
                self.raw_data[scn]["wind_speed"]
            ], axis=1)

            # Daily values (assume monthly average = daily)
            Tmax = df["max_temp"].values
            Tmin = df["min_temp"].values
            Rs = df["solar_radiation"].values  # kWh/m²/day
            RH = df["relative_humidity"].values
            u2 = df["wind_speed"].values

            # Solar declination, daylight hours, etc.
            J = df.index.dayofyear.values
            lat_rad = np.radians(self.lat)

            # Solar declination
            delta = 0.409 * np.sin(2 * np.pi * J / 365 - 1.39)
            # Sunset hour angle
            ws = np.arccos(-np.tan(lat_rad) * np.tan(delta))
            # Extraterrestrial radiation (Ra)
            dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)
            Ra = (24 * 60 / np.pi) * 0.0820 * dr * (
                ws * np.sin(lat_rad) * np.sin(delta) +
                np.cos(lat_rad) * np.cos(delta) * np.sin(ws)
            )  # MJ/m²/day

            # Clear-sky radiation (Rso)
            Rso = (0.75 + 2e-5 * 500) * Ra  # elevation ~500m approx

            # Net radiation (Rn)
            Rns = 0.77 * Rs * 3.6  # Rs in kWh → MJ
            sigma = 2.04e-10  # MJ/m²/K⁴/day
            Tmean = (Tmax + Tmin) / 2 + 273.15
            Rnl = sigma * (Tmax + 273.15)**4 - sigma * (Tmin + 273.15)**4
            Rnl *= (0.34 - 0.14 * np.sqrt(RH / 100)) * (1.35 * Rs / Rso - 0.35)
            Rn = Rns - Rnl

            # Psychrometric constant
            gamma = 0.665e-3 * 101.3  # kPa/°C (sea level)

            # Saturation vapor pressure
            es = 0.6108 * np.exp(17.27 * Tmean / (Tmean + 237.3))
            ea = es * RH / 100

            # Delta (slope of saturation curve)
            delta_s = 4098 * es / (Tmean + 237.3)**2

            # ET₀
            numerator = 0.408 * delta_s * (Rn - 0) + gamma * (37 / (Tmean - 35)) * u2 * (es - ea)
            denominator = delta_s + gamma * (1 + 0.34 * u2)
            et0 = np.where(denominator != 0, numerator / denominator, np.nan)

            et0_df = pd.DataFrame({"ET0_mm_day": et0}, index=df.index)
            self.et0[scn] = et0_df

    # ------------------------------------------------------------------
    # 3. CROP WATER REQUIREMENT & BALANCE
    # ------------------------------------------------------------------
    def crop_water_requirement(self, crop: str, kc_monthly: Optional[List[float]] = None):
        """
        CWR = Kc × ET₀
        kc_monthly: list of 12 values (Jan–Dec), else use single Kc from library
        """
        if crop not in self.CROP_KC and kc_monthly is None:
            raise ValueError(f"Unknown crop: {crop}. Use kc_monthly or add to CROP_KC.")

        self.cwr = {}
        for scn in self.et0:
            et0 = self.et0[scn]["ET0_mm_day"]
            if kc_monthly:
                kc_series = pd.Series(
                    np.tile(kc_monthly, len(et0) // 12 + 1)[:len(et0)],
                    index=et0.index
                )
            else:
                kc = self.CROP_KC[crop]
                kc_series = pd.Series(kc, index=et0.index)

            cwr = et0 * kc_series
            self.cwr[scn] = pd.DataFrame({"CWR_mm_day": cwr}, index=et0.index)

    def water_balance(self):
        """Irrigation Need = CWR - Precipitation (positive = need irrigation)"""
        self.balance = {}
        for scn in self.cwr:
            if "precipitation" not in self.raw_data[scn]:
                continue
            precip = self.raw_data[scn]["precipitation"]["precipitation"]
            cwr = self.cwr[scn]["CWR_mm_day"]
            df = pd.concat([precip, cwr], axis=1).dropna()
            df["irrigation_need"] = df["CWR_mm_day"] - df["precipitation"]
            df["surplus_deficit"] = df["precipitation"] - df["CWR_mm_day"]
            self.balance[scn] = df[["irrigation_need", "surplus_deficit"]]

    # ------------------------------------------------------------------
    # 4. INSIGHTS
    # ------------------------------------------------------------------
    def compute_insights(self):
        self.insights = {}
        for scn in self.raw_data:
            self.insights[scn] = {}
            for p in self.raw_data[scn]:
                df = self.raw_data[scn][p]
                yearly = df.resample("Y").mean()
                mean_val = df.mean().iloc[0]
                max_val = df.max().iloc[0]
                min_val = df.min().iloc[0]
                if len(yearly) >= 5:
                    x = np.arange(len(yearly))
                    slope, _, _, p, _ = linregress(x, yearly.iloc[:, 0])
                    trend_decade = slope * 10
                else:
                    trend_decade, p = np.nan, np.nan
                baseline = df["1981":"2000"].mean().iloc[0] if "1981" in df.index.year else np.nan
                future = df["2081":"2100"].mean().iloc[0] if "2081" in df.index.year else np.nan
                change = future - baseline if not (np.isnan(baseline) or np.isnan(future)) else np.nan

                self.insights[scn][p] = {
                    "mean": round(mean_val, 2),
                    "trend_per_decade": round(trend_decade, 3) if not np.isnan(trend_decade) else None,
                    "p_value": round(p, 4) if not np.isnan(p) else None,
                    "projected_change": round(change, 2) if not np.isnan(change) else None,
                }

        # Add ET₀ and CWR insights
        for scn in self.et0:
            if scn not in self.insights:
                self.insights[scn] = {}
            et0_y = self.et0[scn].resample("Y").mean()
            self.insights[scn]["ET0"] = {
                "mean": round(self.et0[scn].mean().iloc[0], 2),
                "trend_per_decade": round(linregress(np.arange(len(et0_y)), et0_y.iloc[:,0])[0]*10, 3),
            }
            if scn in self.cwr:
                cwr_y = self.cwr[scn].resample("Y").mean()
                self.insights[scn]["CWR"] = {
                    "mean": round(self.cwr[scn].mean().iloc[0], 2),
                }

    def print_insights(self):
        print("\n" + "=" * 70)
        print("SOLAR, CLIMATE & CROP WATER INSIGHTS")
        print("=" * 70)
        for scn in self.insights:
            print(f"\nScenario: {scn.upper()}")
            for p, s in self.insights[scn].items():
                unit = {
                    "solar_radiation": "kWh/m²/day",
                    "temperature": "°C",
                    "precipitation": "mm/day",
                    "ET0": "mm/day",
                    "CWR": "mm/day"
                }.get(p, "")
                print(f"  • {p.replace('_', ' ').title()}: Mean = {s['mean']} {unit}")
                if "trend_per_decade" in s and s["trend_per_decade"] is not None:
                    print(f"      Trend: {s['trend_per_decade']} {unit}/decade")

    # ------------------------------------------------------------------
    # 5. PLOTLY VISUALISATIONS
    # ------------------------------------------------------------------
    def plot_crop_water(self, crop: str):
        """Plot ET₀, CWR, Precip, Irrigation Need"""
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=("Solar Radiation", "ET₀ (Reference)", f"CWR ({crop.title()})", "Water Balance"),
            shared_xaxes=True,
            vertical_spacing=0.05
        )

        colors = {"historical": "#2E2E2E", "ssp245": "#E67E22", "ssp585": "#C0392B"}

        for row, (param, title) in enumerate([
            ("solar_radiation", "Solar Radiation (kWh/m²/day)"),
            ("ET0", "ET₀ (mm/day)"),
            ("CWR", f"CWR {crop.title()} (mm/day)"),
            ("irrigation_need", "Irrigation Need (mm/day)")
        ], 1):
            for scn in self.SCENARIOS:
                if scn not in self.raw_data:
                    continue
                if param == "ET0" and scn in self.et0:
                    data = self.et0[scn].resample("Y").mean()
                elif param == "CWR" and scn in self.cwr:
                    data = self.cwr[scn].resample("Y").mean()
                elif param == "irrigation_need" and scn in self.balance:
                    data = self.balance[scn][["irrigation_need"]].resample("Y").mean()
                elif param in self.raw_data[scn]:
                    data = self.raw_data[scn][param].resample("Y").mean()
                else:
                    continue

                fig.add_trace(
                    go.Scatter(
                        x=data.index, y=data.iloc[:,0],
                        name=scn.upper(), line=dict(color=colors[scn]),
                        legendgroup=scn, showlegend=(row == 1)
                    ),
                    row=row, col=1
                )

        fig.update_layout(height=900, title=f"FAO-56 Crop Water: {crop.title()} @ ({self.lat}, {self.lon})")
        fig.show()


# --------------------------------------------------------------
# EXAMPLE: Maize in Northern Kenya
# --------------------------------------------------------------
if __name__ == "__main__":
    proj = SolarAgriProjector(latitude=2.5, longitude=37.9)

    # 1. Fetch required data
    proj.fetch([
        "solar_radiation", "max_temp", "min_temp",
        "precipitation", "relative_humidity", "wind_speed"
    ])

    # 2. Compute ET₀
    proj.compute_fao56_et0()

    # 3. Crop Water Requirement (Maize)
    proj.crop_water_requirement(crop="maize")

    # 4. Water Balance
    proj.water_balance()

    # 5. Insights
    proj.compute_insights()
    proj.print_insights()

    # 6. Interactive Plot
    proj.plot_crop_water(crop="maize")