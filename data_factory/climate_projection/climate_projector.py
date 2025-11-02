# --------------------------------------------------------------
#  NASA POWER + FAO-56 Crop Water Requirement Calculator (Plotly)
# --------------------------------------------------------------
import requests
import pandas as pd
import numpy as np
import requests_cache
from datetime import timedelta
from scipy.stats import linregress
import plotly.graph_objects as go
from plotly.subplots import make_subplots



from typing import List, Dict, Optional, Tuple


class SolarAgriProjector:
    """
    NASA POWER + FAO-56 Crop Water Requirement (ET₀, CWR, Irrigation Need)
    Interactive Plotly visualisations.
    """
    BASE_URL = "https://power.larc.nasa.gov/api/projection/daily/point"
    PARAMETERS = "ALLSKY_SFC_SW_DWN,T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS10M"

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

    requests_cache.install_cache(
        "nasa_power_cache",                 # cache name (sqlite by default)
        expire_after=timedelta(days=30),    # cache expiration
        allowable_methods=["GET"],          # cache GET requests
        stale_if_error=True                 # use stale cache if request fails
    )

    def __init__(self, nasa_params: Dict):
        self.name = nasa_params["name"]
        self.lat = float(nasa_params["lat"])
        self.lon = float(nasa_params["lon"])
        self.ts = nasa_params["timestandard"]
        self.community = nasa_params["community"]
        self.model = nasa_params["model"]
        self.scenario = nasa_params["scenario"]
        self.start = nasa_params["start"]
        self.end = nasa_params["end"]


    # ------------------------------------------------------------------
    # 1. FETCH DATA
    # ------------------------------------------------------------------
   

    # Initialize requests_cache globally (e.g., once in your class __init__ or module)
    

    def fetch_nasa_projections(self) -> pd.DataFrame:
        """
        Fetch NASA POWER projections with caching via requests_cache.
        """
        params = {
            "user": self.name,
            "latitude": self.lat,
            "longitude": self.lon,
            "community": self.community,
            "parameters": self.PARAMETERS,
            "scenario": self.scenario,
            "model": self.model,
            "time-standard": self.ts,
            "format": "json",
            "start": self.start,
            "end": self.end,
        }

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=30)
            r.raise_for_status()
            payload = r.json()

            coords = payload.get("geometry", {}).get("coordinates", [self.lon, self.lat, None])
            lon, lat, elev = coords if len(coords) == 3 else (self.lon, self.lat, None)
            parameters_info = payload.get("parameters", {})  # optional

            all_dfs = []
            data_block = payload.get("properties", {}).get("parameter", {})

            for param, values in data_block.items():
                df = pd.DataFrame.from_dict(values, orient="index", columns=["value"])
                df.index = pd.to_datetime(df.index, format="%Y%m%d")
                df.reset_index(inplace=True)
                df.rename(columns={"index": "date"}, inplace=True)

                df["value"] = df["value"].replace(-999.0, pd.NA)

                if df["value"].isna().all():
                    print(f"Skipping {param}: all values missing.")
                    continue

                df["parameter"] = param
                df["units"] = parameters_info.get(param, {}).get("units", "")
                df["lon"] = lon
                df["lat"] = lat
                df["elev"] = elev
                df["source"] = "NASA_POWER"

                all_dfs.append(df[["date", "parameter", "value", "units", "lon", "lat", "elev", "source"]])

            if all_dfs:
                df_final = pd.concat(all_dfs, ignore_index=True)
                # Inform if cached
                if getattr(r, "from_cache", False):
                    print("[Cache Hit] Loaded data from requests_cache.")
                else:
                    print("[Cache Miss] Fetched new data from NASA POWER.")
                return df_final
            else:
                print("No valid data returned.")
                return pd.DataFrame(columns=["date", "parameter", "value", "units", "lon", "lat", "elev", "source"])

        except Exception as e:
            print(f"[Fetch Failed]: {e}")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # 2. FAO-56 PENMAN-MONTEITH ET₀
    # ------------------------------------------------------------------
    def compute_fao56_et0(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute Reference Evapotranspiration (ET₀) using FAO-56 Penman–Monteith method.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame returned by fetch_nasa_projections(), expected to contain
            columns: ['date', 'parameter', 'value', 'units', 'lon', 'lat', 'elev', 'source'].

        Returns
        -------
        pd.DataFrame
            A DataFrame with ['date', 'ET0_mm_day'] columns.
        """

        # Pivot to wide format (parameters as columns)
        df_wide = df.pivot(index="date", columns="parameter", values="value").sort_index()

        # Required NASA parameters
        try:
            Tmax = df_wide["T2M_MAX"].astype(float).values
            Tmin = df_wide["T2M_MIN"].astype(float).values
            Rs = df_wide["ALLSKY_SFC_SW_DWN"].astype(float).values  # MJ/m²/day
            RH = df_wide["RH2M"].astype(float).values
            u2 = df_wide["WS10M"].astype(float).values
        except KeyError as e:
            print(f"[Missing data] {e} not found in dataset.")
            return pd.DataFrame(columns=["date", "ET0_mm_day"])

        # Compute required variables
        Tmean = (Tmax + Tmin) / 2.0
        lat = getattr(self, "lat", 0.0)
        elev = getattr(self, "elev", 500.0)

        # Step 1: Atmospheric pressure & psychrometric constant
        P = 101.3 * ((293.0 - 0.0065 * elev) / 293.0) ** 5.26
        gamma = 0.000665 * P

        # Step 2: Saturation and actual vapor pressure
        es = 0.6108 * np.exp(17.27 * Tmean / (Tmean + 237.3))
        ea = es * RH / 100.0

        # Step 3: Slope of vapor pressure curve
        delta_s = 4098 * es / (Tmean + 237.3) ** 2

        # Step 4: Radiation terms
        J = df_wide.index.dayofyear.values
        lat_rad = np.radians(lat)
        delta = 0.409 * np.sin(2 * np.pi * J / 365 - 1.39)
        ws = np.arccos(-np.tan(lat_rad) * np.tan(delta))
        dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)
        Ra = (24 * 60 / np.pi) * 0.0820 * dr * (
            ws * np.sin(lat_rad) * np.sin(delta)
            + np.cos(lat_rad) * np.cos(delta) * np.sin(ws)
        )
        Rso = (0.75 + 2e-5 * elev) * Ra
        Rns = 0.77 * Rs
        sigma = 4.903e-9  # MJ·K⁻⁴·m⁻²·day⁻¹
        Rnl = sigma * ((Tmax + 273.16) ** 4 + (Tmin + 273.16) ** 4) / 2.0
        Rnl *= (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * (Rs / Rso) - 0.35)
        Rn = Rns - Rnl

        # Step 5: ET₀ computation (mm/day)
        numerator = 0.408 * delta_s * Rn + gamma * (900 / (Tmean + 273)) * u2 * (es - ea)
        denominator = delta_s + gamma * (1 + 0.34 * u2)
        et0 = np.where(denominator != 0, numerator / denominator, np.nan)

        # Return result
        et0_df = pd.DataFrame({"date": df_wide.index, "ET0_mm_day": et0})
        return et0_df



    def crop_water_requirement(self, df_et0: pd.DataFrame, crop: str,
                           kc_monthly: Optional[List[float]] = None) -> pd.DataFrame:
        """
        Compute Crop Water Requirement (CWR = Kc × ET₀).
        Parameters
        ----------
        df_et0 : pd.DataFrame
            DataFrame with ['date', 'ET0_mm_day'].
        crop : str
            Crop name to use for Kc lookup.
        kc_monthly : list[float], optional
            12 monthly Kc values (Jan–Dec). Overrides default crop Kc if provided.
        """
        if crop not in self.CROP_KC and kc_monthly is None:
            raise ValueError(f"Unknown crop: {crop}. Use kc_monthly or add to CROP_KC.")

        df = df_et0.copy()
        df["month"] = df["date"].dt.month

        if kc_monthly:
            if len(kc_monthly) != 12:
                raise ValueError("kc_monthly must have exactly 12 monthly values.")
            kc_map = {m + 1: kc_monthly[m] for m in range(12)}
        else:
            kc_val = self.CROP_KC[crop]
            if isinstance(kc_val, (int, float)):
                kc_map = {m: kc_val for m in range(1, 13)}
            else:
                # Allow per-month Kc in library too
                kc_map = {m + 1: kc_val[m] for m in range(12)}

        df["Kc"] = df["month"].map(kc_map)
        df["CWR_mm_day"] = df["ET0_mm_day"] * df["Kc"]

        return df[["date", "ET0_mm_day", "Kc", "CWR_mm_day"]]

    def water_balance(self, df_cwr: pd.DataFrame, df_nasa: pd.DataFrame) -> pd.DataFrame:
        """
        Compute irrigation need = CWR - precipitation.
        Positive => irrigation required.
        """
        df_pivot = df_nasa.pivot(index="date", columns="parameter", values="value").sort_index()

        if "PRECTOTCORR" not in df_pivot.columns:
            raise ValueError("Precipitation data (PRECTOTCORR) missing from NASA dataset.")

        df = pd.merge(df_cwr, df_pivot[["PRECTOTCORR"]], on="date", how="left")
        df.rename(columns={"PRECTOTCORR": "precip_mm_day"}, inplace=True)

        # Compute irrigation need
        df["irrigation_need_mm_day"] = df["CWR_mm_day"] - df["precip_mm_day"]
        df["surplus_deficit_mm_day"] = df["precip_mm_day"] - df["CWR_mm_day"]

        # Optional: aggregate monthly totals
        df["month"] = df["date"].dt.to_period("M")
        df_monthly = (
            df.groupby("month")[["ET0_mm_day", "CWR_mm_day", "precip_mm_day",
                                 "irrigation_need_mm_day", "surplus_deficit_mm_day"]]
            .mean()
            .reset_index()
        )

        return df_monthly


    def compute_insights(self, raw_data, et0, cwr, balance):
        """
        Compute comprehensive insights for one scenario using your provided DataFrames:
          - raw_data: pd.DataFrame with 'date', 'parameter', 'value'
          - et0: pd.DataFrame with 'date', 'ET0_mm_day'
          - cwr: pd.DataFrame with 'date', 'CWR_mm_day'
          - balance: pd.DataFrame with 'month', 'irrigation_need_mm_day'

        Output:
          self.insights: dict of metrics for each parameter and derived variables
        """

        def _annual_series(ts, agg="mean"):
            return ts.resample("YE").sum() if agg == "sum" else ts.resample("YE").mean()

        def _trend_per_decade(ts):
            ts = ts.dropna()
            if len(ts) < 5:
                return None, None
            x = np.arange(len(ts))
            slope, _, _, pval, _ = linregress(x, ts.values)
            return slope * 10, pval

        def _period_mean(ts, start_year, end_year):
            mask = (ts.index.year >= start_year) & (ts.index.year <= end_year)
            return ts.loc[mask].mean() if mask.any() else None

        def _seasonal_climatology(ts):
            return ts.groupby(ts.index.month).mean().reindex(range(1, 13))

        insights = {}

        # --- Raw data parameters ---
        raw_data["date"] = pd.to_datetime(raw_data["date"])
        for param, grp in raw_data.groupby("parameter"):
            s = grp.set_index("date")["value"].sort_index()
            if s.empty:
                continue
            is_precip = "precip" in param.lower()
            annual = _annual_series(s, agg="sum" if is_precip else "mean")
            trend, pval = _trend_per_decade(annual)
            season = _seasonal_climatology(s)
            baseline = _period_mean(s, 1981, 2000)
            future = _period_mean(s, 2081, 2100)
            projected_change = future - baseline if baseline is not None and future is not None else None
            pct10, pct90 = np.nanpercentile(s, [10, 90])
            insights[param] = {
                "mean": round(s.mean(), 3),
                "median": round(s.median(), 3),
                "std": round(s.std(), 3),
                "min": round(s.min(), 3),
                "min_date": str(s.idxmin().date()),
                "max": round(s.max(), 3),
                "max_date": str(s.idxmax().date()),
                "pct10": round(pct10, 3),
                "pct90": round(pct90, 3),
                "seasonal_climatology_monthly": {m: round(v, 3) for m, v in season.items()},
                "annual_mean_or_sum": round(float(annual.mean()), 3),
                "trend_per_decade": round(trend, 4) if trend else None,
                "trend_p_value": round(pval, 4) if pval else None,
                "baseline_1981_2000_mean": round(baseline, 3) if baseline is not None else None,
                "future_2081_2100_mean": round(future, 3) if future is not None else None,
                "projected_change_2081_2100_vs_1981_2000": round(projected_change, 3) if projected_change else None,
            }

        # --- ET0 ---
        et0["date"] = pd.to_datetime(et0["date"])
        s = et0.set_index("date")["ET0_mm_day"].sort_index()
        annual = _annual_series(s)
        trend, pval = _trend_per_decade(annual)
        season = _seasonal_climatology(s)
        insights["ET0"] = {
            "mean_mm_day": round(s.mean(), 3),
            "annual_mean_mm_day": round(annual.mean(), 3),
            "trend_per_decade_mm_day": round(trend, 4) if trend else None,
            "trend_p_value": round(pval, 4) if pval else None,
            "seasonal_peak_month": int(season.idxmax()),
            "seasonal_climatology": {m: round(v, 3) for m, v in season.items()},
        }

        # --- CWR ---
        cwr["date"] = pd.to_datetime(cwr["date"])
        s = cwr.set_index("date")["CWR_mm_day"].sort_index()
        annual = _annual_series(s, agg="sum")
        trend, pval = _trend_per_decade(_annual_series(s))
        season = _seasonal_climatology(s)
        insights["CWR"] = {
            "mean_mm_day": round(s.mean(), 3),
            "annual_total_mm_year": round(annual.mean(), 3),
            "trend_per_decade_mm_day": round(trend, 4) if trend else None,
            "trend_p_value": round(pval, 4) if pval else None,
            "seasonal_peak_month": int(season.idxmax()),
            "seasonal_climatology": {m: round(v, 3) for m, v in season.items()},
        }

        # --- Irrigation balance ---
        balance["month"] = balance["month"].dt.to_timestamp()
        s = balance.set_index("month")["irrigation_need_mm_day"].sort_index()
        monthly = s.resample("M").mean()
        months_need = int((monthly > 0).sum())
        pct_months_need = 100.0 * months_need / max(len(monthly), 1)
        insights["IrrigationBalance"] = {
            "mean_irrigation_need_mm_day": round(s.mean(), 3),
            "annual_mean_need_mm_day": round(_annual_series(s).mean(), 3),
            "months_per_year_with_need": months_need,
            "percent_months_need": round(pct_months_need, 1),
            "mean_deficit_mm_day_when_needed": round(monthly[monthly > 0].mean(), 3) if (monthly > 0).any() else 0,
            "max_monthly_deficit_mm_day": round(monthly.max(), 3),
            "worst_month_date": str(monthly.idxmax().date()),
        }

        return insights



    def run_simulation(self):
        nasa_data = self.fetch_nasa_projections()
        et0_df = self.compute_fao56_et0(nasa_data)
        cwr_df = self.crop_water_requirement(et0_df, crop="maize")
        balance_df = self.water_balance(cwr_df, nasa_data)
        insights = self.compute_insights(nasa_data, et0_df, cwr_df, balance_df)

        return {
            "raw_data": nasa_data,
            "et0_df": et0_df,
            "cwr_df": cwr_df,
            "balance_df": balance_df,
            "insights": insights,
        }
        
