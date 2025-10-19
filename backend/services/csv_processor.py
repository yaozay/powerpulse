import os
import pandas as pd
from datetime import datetime, timedelta, timezone 
from pathlib import Path
from typing import List, Dict  
import numpy as np 

class EnergyDataProcessor:
    """
    Processes energy consumption CSV data and calculates dashboard metrics
    """

   
    def get_7d_forecast(self, home_id: int = 1):
        """
        7-day forecast using:
          - Weekday average from the last ~8 weeks (seasonality)
          - Simple linear trend from the last ~28 days (direction)
        Combines them additively:
            forecast = weekday_avg + (trend_pred - recent_mean)
        """
        if self.df is None:
            self.load_data()

        df = self.df[self.df["Home ID"] == home_id].copy()
        today = datetime.now().date()

        # No data -> zeros
        if df.empty:
            return [
                {"date": (today + timedelta(days=i+1)).isoformat(),
                 "weekday": (today + timedelta(days=i+1)).strftime("%a"),
                 "kwh": 0.0, "cost_usd": 0.0, "co2_kg": 0.0}
                for i in range(7)
            ]

        # --- Daily totals ---
        df["date"] = df["datetime"].dt.date
        daily = df.groupby("date", as_index=False)["Energy Consumption (kWh)"].sum()
        daily.rename(columns={"Energy Consumption (kWh)": "kwh"}, inplace=True)
        daily = daily.sort_values("date")

        # --- Weekday seasonality (use last ~8 weeks if available) ---
        cutoff8w = pd.Timestamp(today - timedelta(days=56)).date()
        hist8 = daily[daily["date"] >= cutoff8w].copy()
        if hist8.empty:
            hist8 = daily.copy()
        hist8["weekday_idx"] = pd.to_datetime(hist8["date"]).dt.weekday  # 0=Mon
        weekday_avg = hist8.groupby("weekday_idx")["kwh"].mean()
        overall_mean = float(hist8["kwh"].mean()) if not hist8.empty else float(daily["kwh"].mean())

        # --- Trend (simple linear regression over last ~28 days) ---
        cutoff4w = pd.Timestamp(today - timedelta(days=28)).date()
        hist4 = daily[daily["date"] >= cutoff4w].copy()
        if hist4.empty:
            hist4 = daily.copy()

        # x = 0..n-1, y = kwh
        y = hist4["kwh"].to_numpy(dtype=float)
        x = np.arange(len(y), dtype=float)
        if len(y) >= 2:
            slope, intercept = np.polyfit(x, y, 1)
        else:
            slope, intercept = 0.0, float(y.mean()) if len(y) else 0.0

        # average tariff & CO2 factor
        if "Tariff ($/kWh)" in df.columns:
            tariff = float(df["Tariff ($/kWh)"].dropna().mean() or 0.12)
        else:
            tariff = 0.12

        out = []
        n0 = len(y)  # next x index starts after the last observed day
        for i in range(1, 8):
            d = today + timedelta(days=i)
            wd = d.weekday()

            # Seasonal baseline
            wd_avg = float(weekday_avg.get(wd, overall_mean))

            # Trend prediction for that future day
            trend_pred = float(intercept + slope * (n0 + i))

            # Combine (additive): shift weekday baseline by trend deviation from mean
            kwh = wd_avg + (trend_pred - overall_mean)
            kwh = max(0.0, round(kwh, 2))

            cost = round(kwh * tariff, 2)
            co2 = round(kwh * self.grid_emissions_kg_per_kwh, 2)

            out.append({
                "date": d.isoformat(),
                "weekday": d.strftime("%a"),
                "kwh": kwh,
                "cost_usd": cost,
                "co2_kg": co2,
            })
        return out  
    
    def get_weather_data(self, home_id: int = 1):
        if self.df is None:
            self.load_data()

        df = self.df
        if 'Home ID' in df.columns:
            home_df = df[df['Home ID'] == home_id].copy()
        else:
            home_df = df.copy()

        if home_df.empty:
            return {
                "temperature_f": 0,
                "temperature_c": 0,
                "indoor_temperature_c": 0,
                "location": f"Home {home_id} (No data)",
            }

        latest = home_df.sort_values("datetime", ascending=False).iloc[0]

        city   = str(latest.get("Location City", "") or "").strip()
        region = str(latest.get("Location Region", "") or "").strip()
        # fallback to most frequent values if latest is blank
        if not city and "Location City" in home_df.columns and not home_df["Location City"].dropna().empty:
            city = str(home_df["Location City"].mode().iloc[0]).strip()
        if not region and "Location Region" in home_df.columns and not home_df["Location Region"].dropna().empty:
            region = str(home_df["Location Region"].mode().iloc[0]).strip()

        location = ", ".join([p for p in (city, region) if p]) or f"Home {home_id}"

        out_c = float(latest.get("Outdoor Temperature (C)", 0) or 0)
        in_c  = float(latest.get("Indoor Temperature (C)", 0) or 0)
        temp_f = (out_c * 9/5) + 32

        return {
            "temperature_f": round(temp_f),
            "temperature_c": round(out_c, 1),
            "indoor_temperature_c": round(in_c, 1),
            "location": location,
        }

    def get_weather_forecast_7d(self, home_id: int = 1):
        if self.df is None:
            self.load_data()

        df = self.df[self.df["Home ID"] == home_id].copy()
        if df.empty or "Outdoor Temperature (C)" not in df.columns:
            today = datetime.now().date()
            return [{
                "date": (today + timedelta(days=i+1)).isoformat(),
                "weekday": (today + timedelta(days=i+1)).strftime("%a"),
                "temp_c": 0.0,
                "temp_f": 32.0,
            } for i in range(7)]

        if "datetime" not in df.columns or not pd.api.types.is_datetime64_any_dtype(df["datetime"]):
            df["datetime"] = pd.to_datetime(
                df["Date"].astype(str) + " " + df["Time"].astype(str),
                format="%m/%d/%y %H:%M",
                errors="coerce"
            )

        df = df.dropna(subset=["datetime"]).copy()
        df["date"] = df["datetime"].dt.date

        daily = df.groupby("date", as_index=False)["Outdoor Temperature (C)"].mean()
        daily = daily.rename(columns={"Outdoor Temperature (C)": "temp_c"})

        cutoff = pd.Timestamp(datetime.now() - timedelta(days=56)).date()
        hist = daily[daily["date"] >= cutoff].copy()
        if hist.empty:
            hist = daily.copy()

        hist["weekday_idx"] = pd.to_datetime(hist["date"]).dt.weekday
        weekday_avg_c = hist.groupby("weekday_idx")["temp_c"].mean()
        fallback = float(hist["temp_c"].mean() if not hist.empty else 0.0)

        today = datetime.now().date()
        out = []
        for i in range(1, 8):
            d = today + timedelta(days=i)
            c = float(weekday_avg_c.get(d.weekday(), fallback))
            out.append({
                "date": d.isoformat(),
                "weekday": d.strftime("%a"),
                "temp_c": round(c, 1),
                "temp_f": round((c * 9/5) + 32),
            })
        return out
    
    def get_device_stats(self, home_id: int, appliance_type: str) -> dict:
        if self.df is None:
            self.load_data()

        df_home = self.df[self.df["Home ID"] == home_id].copy()
        if df_home.empty:
            return {"appliance_type": appliance_type, "daily_kwh": 0.0, "monthly_kwh": 0.0,
                    "avg_runtime_hours": 0.0, "peak_hour": None}

        # Normalize labels once
        df_home["__appliance_norm"] = df_home["Appliance Type"].astype(str).str.strip().str.casefold()
        target_norm = str(appliance_type).strip().casefold()

        # 1) exact (case-insensitive) match
        df = df_home[df_home["__appliance_norm"] == target_norm]

        # 2) partial match (target in csv label OR csv label in target)
        if df.empty:
            contains1 = df_home["__appliance_norm"].str.contains(rf"\b{target_norm}\b", na=False)
            contains2 = contains1 | df_home["__appliance_norm"].apply(lambda s: target_norm in s)
            df = df_home[contains2]

        # 3) closest string (Levenshtein-lite)
        if df.empty:
            candidates = df_home["__appliance_norm"].unique().tolist()
            best = difflib.get_close_matches(target_norm, candidates, n=1, cutoff=0.6)
            if best:
                df = df_home[df_home["__appliance_norm"] == best[0]]

        if df.empty:
            return {"appliance_type": appliance_type, "daily_kwh": 0.0, "monthly_kwh": 0.0,
                    "avg_runtime_hours": 0.0, "peak_hour": None}

        # Keep original label for display
        label = str(df["Appliance Type"].iloc[0]).strip()

        # Chrono helpers
        df = df.sort_values("datetime")
        df["date"] = df["datetime"].dt.date
        df["year"] = df["datetime"].dt.year
        df["month"] = df["datetime"].dt.month

        # Daily (latest day)
        latest_date = df["date"].max()
        daily_kwh = float(df.loc[df["date"] == latest_date, "Energy Consumption (kWh)"].sum())

        # Monthly (month of latest reading)
        latest_year, latest_month = int(df.iloc[-1]["year"]), int(df.iloc[-1]["month"])
        monthly_kwh = float(
            df.loc[(df["year"] == latest_year) & (df["month"] == latest_month), "Energy Consumption (kWh)"].sum()
        )

        # Avg runtime = (#active samples) * (median sampling interval)
        active_mask = df["Energy Consumption (kWh)"] > 0.01
        diffs = df["datetime"].diff().dropna()
        median_interval_hours = (np.median(diffs.dt.total_seconds()) / 3600.0) if not diffs.empty else 0.0
        avg_runtime_hours = float(active_mask.sum() * median_interval_hours)

        # Peak hour (prefer last 30d)
        horizon_start = df["datetime"].max() - timedelta(days=30)
        recent = df[df["datetime"] >= horizon_start]
        if recent.empty:
            recent = df
        recent = recent.copy()
        recent["hour"] = recent["datetime"].dt.hour
        hour_means = recent.groupby("hour")["Energy Consumption (kWh)"].mean()
        peak_hour = None
        if not hour_means.empty:
            h = int(hour_means.idxmax())
            peak_hour = f"{h:02d}:00–{(h+1)%24:02d}:00"

        return {
            "appliance_type": label,
            "daily_kwh": round(daily_kwh, 3),
            "monthly_kwh": round(monthly_kwh, 3),
            "avg_runtime_hours": round(avg_runtime_hours, 2),
            "peak_hour": peak_hour,
        }

    def get_devices(self, home_id: int) -> List[Dict]:
        """
        Return latest snapshot per appliance for a home:
          - appliance_type
          - last_kwh
          - last_seen_iso (ISO 8601)
          - device_smartness ('Smart' | 'Not Smart' | 'Unknown')
          - is_online (True if last seen within 24h)
        """
        if self.df is None:
            self.load_data()

        df = self.df[self.df['Home ID'] == home_id].copy()
        if df.empty:
            return []

        # Ensure expected columns exist
        for col in ["Appliance Type", "Energy Consumption (kWh)", "Device Smartness", "datetime"]:
            if col not in df.columns:
                raise ValueError(f"Missing column in CSV: {col}")

        # Sort newest first within each appliance then take first row per appliance
        df = df.sort_values(["Appliance Type", "datetime"], ascending=[True, False])
        latest = df.groupby("Appliance Type", as_index=False).first()

        now = datetime.now(timezone.utc)
        out: List[Dict] = []
        for _, row in latest.iterrows():
            dt = row["datetime"]
            # treat existing naive timestamps as UTC for consistency
            if isinstance(dt, datetime) and dt.tzinfo is None:
                dt_utc = dt.replace(tzinfo=timezone.utc)
            else:
                dt_utc = dt

            last_seen_iso = dt_utc.isoformat() if isinstance(dt_utc, datetime) else None
            is_online = False
            if isinstance(dt_utc, datetime):
                is_online = (now - dt_utc) <= timedelta(hours=24)

            smart_raw = str(row.get("Device Smartness", "Unknown")).strip()
            smart = smart_raw if smart_raw in ("Smart", "Not Smart", "Unknown") else "Unknown"

            try:
                last_kwh = round(float(row.get("Energy Consumption (kWh)", 0.0)), 3)
            except Exception:
                last_kwh = 0.0

            out.append({
                "appliance_type": str(row["Appliance Type"]).strip(),
                "last_kwh": last_kwh,
                "last_seen_iso": last_seen_iso,
                "device_smartness": smart,
                "is_online": is_online,
            })

        # Stable sort for UI
        out.sort(key=lambda d: d["appliance_type"].lower())
        return out
    
    def __init__(self, csv_path: str = None):
        # Handle relative paths from services/ directory
        if csv_path is None:
            # Default: look for CSV relative to this file's location
            current_dir = Path(__file__).parent.parent  # Go up from services/ to backend/
            csv_path = current_dir / "data" / "powerpulse-datas.csv"
        
        self.csv_path = str(csv_path)
        self.df = None
        self.grid_emissions_kg_per_kwh = 0.45  # Texas grid average
        
    def load_data(self):
        """Load and parse CSV data"""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV file not found at {self.csv_path}")
        
        self.df = pd.read_csv(self.csv_path)

        if 'Home ID' in self.df.columns:
            self.df['Home ID'] = pd.to_numeric(self.df['Home ID'], errors='coerce').astype('Int64')

        self.df['datetime'] = pd.to_datetime(self.df['Date'] + ' ' + self.df['Time'], format='%m/%d/%y %H:%M')
        
        self.df.columns = self.df.columns.astype(str).str.strip()
        if 'Location City' in self.df.columns:
            self.df['Location City'] = self.df['Location City'].astype(str).str.strip()
        if 'Location Region' in self.df.columns:
            self.df['Location Region'] = self.df['Location Region'].astype(str).str.strip()
        if 'Home ID' in self.df.columns:
            self.df['Home ID'] = pd.to_numeric(self.df['Home ID'], errors='coerce').astype('Int64')
        self.df['datetime'] = pd.to_datetime(
            self.df['Date'].astype(str).str.strip() + ' ' + self.df['Time'].astype(str).str.strip(),
            format='%m/%d/%y %H:%M', errors='coerce'
        )

        # Parse datetime
        self.df['datetime'] = pd.to_datetime(
            self.df['Date'].astype(str) + ' ' + self.df['Time'].astype(str),
            format='%m/%d/%y %H:%M',
            errors='coerce'
        )
        
        # Convert boolean columns
        if 'Occupancy / Motion Detected' in self.df.columns:
            self.df['Occupancy / Motion Detected'] = self.df['Occupancy / Motion Detected'].map({
                'TRUE': True, 'FALSE': False, True: True, False: False
            })
        
        return self.df
    
    def get_current_power(self, home_id: int = 1) -> float:
        """
        Calculate current power draw in kW
        Uses the most recent reading
        """
        if self.df is None:
            self.load_data()
        
        home_data = self.df[self.df['Home ID'] == home_id]
        if home_data.empty:
            return 0.0
        
        # Get most recent entry
        latest = home_data.sort_values('datetime', ascending=False).iloc[0]
        
        # Power (kW) = Voltage (V) × Current (A) / 1000
        if 'Voltage (V)' in latest and 'Current (A)' in latest:
            power_kw = (latest['Voltage (V)'] * latest['Current (A)']) / 1000
            return round(power_kw, 1)
        
        # Fallback: use energy consumption as approximation
        return round(latest['Energy Consumption (kWh)'], 1)
    
    def get_today_usage(self, home_id: int = 1) -> float:
        """
        Calculate today's total energy usage in kWh
        """
        if self.df is None:
            self.load_data()
        
        today = datetime.now().date()
        home_data = self.df[self.df['Home ID'] == home_id].copy()
        home_data['date'] = home_data['datetime'].dt.date
        
        today_data = home_data[home_data['date'] == today]
        
        if today_data.empty:
            # If no data for today, use most recent date's data
            latest_date = home_data['date'].max()
            today_data = home_data[home_data['date'] == latest_date]
        
        total_kwh = today_data['Energy Consumption (kWh)'].sum()
        return round(total_kwh, 1)
    
    def get_today_cost(self, home_id: int = 1) -> float:
        """
        Calculate today's total cost in USD
        """
        if self.df is None:
            self.load_data()
        
        today = datetime.now().date()
        home_data = self.df[self.df['Home ID'] == home_id].copy()
        home_data['date'] = home_data['datetime'].dt.date
        
        today_data = home_data[home_data['date'] == today]
        
        if today_data.empty:
            latest_date = home_data['date'].max()
            today_data = home_data[home_data['date'] == latest_date]
        
        # Cost = Energy (kWh) × Tariff ($/kWh)
        today_data['cost'] = today_data['Energy Consumption (kWh)'] * today_data['Tariff ($/kWh)']
        total_cost = today_data['cost'].sum()
        
        return round(total_cost, 2)
    
    def get_today_co2(self, home_id: int = 1) -> float:
        """
        Calculate today's CO2 emissions in kg
        """
        if self.df is None:
            self.load_data()
        
        today_kwh = self.get_today_usage(home_id)
        co2_kg = today_kwh * self.grid_emissions_kg_per_kwh
        
        return round(co2_kg, 1)
    
    def get_24h_hourly_usage(self, home_id: int = 1):
        """
        Get hourly energy usage for the last 24 hours
        Returns list of {hour, kwh} for chart
        """
        if self.df is None:
            self.load_data()
        
        home_data = self.df[self.df['Home ID'] == home_id].copy()
        
        # Get last 24 hours of data
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        
        recent_data = home_data[home_data['datetime'] >= cutoff].copy()
        
        if recent_data.empty:
            # Use most recent 24 hours of available data
            recent_data = home_data.sort_values('datetime', ascending=False).head(24)
        
        # Group by hour
        recent_data['hour'] = recent_data['datetime'].dt.hour
        hourly = recent_data.groupby('hour')['Energy Consumption (kWh)'].sum().reset_index()
        hourly.columns = ['hour', 'kwh']
        hourly['kwh'] = hourly['kwh'].round(3)
        
        # Format hour as HH:00
        hourly['time'] = hourly['hour'].apply(lambda x: f"{x:02d}:00")
        
        return hourly[['time', 'hour', 'kwh']].to_dict('records')
    
    def get_weather_data(self, home_id: int = 1):
        """
        Get current weather conditions from most recent data
        """
        if self.df is None:
            self.load_data()
        
        home_data = self.df[self.df['Home ID'] == home_id]
        if home_data.empty:
            return None
        
        latest = home_data.sort_values('datetime', ascending=False).iloc[0]
        
        # Convert Celsius to Fahrenheit
        temp_f = (latest['Outdoor Temperature (C)'] * 9/5) + 32
        
        return {
            "temperature_f": round(temp_f),
            "temperature_c": round(latest['Outdoor Temperature (C)'], 1),
            "indoor_temperature_c": round(latest['Indoor Temperature (C)'], 1),
            "humidity": None,  # Not in current CSV
            "wind_speed": None  # Not in current CSV
        }
    
    def get_dashboard_summary(self, home_id: int = 1):
        """
        Get all dashboard metrics in one call
        """
        return {
            "current_power_kw": self.get_current_power(home_id),
            "today_usage_kwh": self.get_today_usage(home_id),
            "today_cost_usd": self.get_today_cost(home_id),
            "today_co2_kg": self.get_today_co2(home_id),
            "hourly_usage_24h": self.get_24h_hourly_usage(home_id),
            "weather": self.get_weather_data(home_id)
        }


# Usage example
if __name__ == "__main__":
    processor = EnergyDataProcessor("backend/data/energy_data.csv")
    
    try:
        processor.load_data()
        print("CSV loaded successfully!")
        print(f"Total rows: {len(processor.df)}")
        print(f"\nColumns: {list(processor.df.columns)}")
        
        # Get dashboard data
        dashboard = processor.get_dashboard_summary(home_id=1)
        
        print("\n=== DASHBOARD METRICS ===")
        print(f"Current Power: {dashboard['current_power_kw']} kW")
        print(f"Today's Usage: {dashboard['today_usage_kwh']} kWh")
        print(f"Today's Cost: ${dashboard['today_cost_usd']}")
        print(f"Today's CO₂: {dashboard['today_co2_kg']} kg")
        
        print("\n=== WEATHER ===")
        if dashboard['weather']:
            print(f"Temperature: {dashboard['weather']['temperature_f']}°F")
            print(f"Indoor: {dashboard['weather']['indoor_temperature_c']}°C")
        
        print("\n=== 24H HOURLY USAGE (sample) ===")
        for entry in dashboard['hourly_usage_24h'][:5]:
            print(f"{entry['time']}: {entry['kwh']} kWh")
            
    except Exception as e:
        print(f"Error: {e}")

        