import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

class EnergyDataProcessor:
    """
    Processes energy consumption CSV data and calculates dashboard metrics
    """
    
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
        
        # Parse datetime
        self.df['datetime'] = pd.to_datetime(
            self.df['Date'] + ' ' + self.df['Time'], 
            format='%m/%d/%y %H:%M'
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