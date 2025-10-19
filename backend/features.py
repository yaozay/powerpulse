import pandas as pd

NUMERIC_FEATURES = [
    "kwh","ma3","ma12","lag1","lag2",
    "temp_out_c","humidity",
    "hour","dayofweek","is_peak",
    "baseline_kwh_per_hour","tariff_usd_per_kwh",
    "home_size_sqft","occupants"
]
CATEGORICAL_FEATURES = ["season","hvac_type","comfort_level"]

def add_time_features(df: pd.DataFrame, ts_col="timestamp") -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df[ts_col].dt.hour
    df["dayofweek"] = df[ts_col].dt.dayofweek
    return df

def add_peak_flag(df: pd.DataFrame, start=15, end=19) -> pd.DataFrame:
    df = df.copy()
    df["is_peak"] = df["hour"].between(start, end).astype(int)
    return df

def add_rollings_lags(df: pd.DataFrame, y_col="kwh") -> pd.DataFrame:
    df = df.sort_values("timestamp").copy()
    df["ma3"]  = df[y_col].rolling(3, min_periods=1).mean()
    df["ma12"] = df[y_col].rolling(12, min_periods=1).mean()
    df["lag1"] = df[y_col].shift(1)
    df["lag2"] = df[y_col].shift(2)
    return df
