from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import joblib

CSV_PATH   = "data/alldata.csv"
MODEL_PATH = "models/ridge_pipeline.pkl"
TS_COL     = "timestamp"

NUMERIC_BASE = [
    "temp_out_c","humidity","baseline_kwh_per_hour","tariff_usd_per_kwh",
    "home_size_sqft","occupants"
]
CATEGORICAL = ["season","hvac_type","comfort_level"]

def build_kwh(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "kwh" not in df.columns:
        if "consumption" not in df.columns:
            raise ValueError("Expected 'consumption' column if 'kwh' is missing.")
        
        cons = df["consumption"].astype(float)
        nondec_ratio = (cons.diff().fillna(0) >= -1e-9).mean()
        if nondec_ratio > 0.95:
            
            kwh = cons.diff()
            kwh[kwh < 0] = np.nan 
            df["kwh"] = kwh
        else:
    
            df["kwh"] = cons


    df[TS_COL] = pd.to_datetime(df[TS_COL], errors="coerce")
    df = df.dropna(subset=[TS_COL, "kwh"]).sort_values(TS_COL)
    if df["kwh"].nunique() <= 2:
        # up-aggregate to 15-minute bins
        df = (
            df.set_index(TS_COL)
              .resample("15min")["kwh"].sum()
              .to_frame()
              .reset_index()
        )
    return df

def add_time_feats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df[TS_COL].dt.hour
    df["dayofweek"] = df[TS_COL].dt.dayofweek
    df["is_peak"] = df["hour"].between(15, 19).astype(int)
    # rollings & lags (past-only)
    df["ma3"]  = df["kwh"].rolling(3, min_periods=1).mean()
    df["ma12"] = df["kwh"].rolling(12, min_periods=1).mean()
    df["lag1"] = df["kwh"].shift(1)
    df["lag2"] = df["kwh"].shift(2)
    return df

def main():
    df = pd.read_csv(CSV_PATH)
    df = build_kwh(df)

    df["kwh_next"] = df["kwh"].shift(-1)

    keep_extra = [c for c in NUMERIC_BASE + CATEGORICAL if c in df.columns]
    df = add_time_feats(df)
    cols = [TS_COL, "kwh", "kwh_next", "ma3","ma12","lag1","lag2","hour","dayofweek","is_peak"] + keep_extra
    df = df.loc[:, [c for c in cols if c in df.columns]].dropna()
    if df["kwh_next"].nunique() <= 2:
        raise ValueError("Target still nearly constant after processing. Check source data or try resampling to 30/60min.")

    numeric_cols = [c for c in ["kwh","ma3","ma12","lag1","lag2","temp_out_c","humidity",
                                "hour","dayofweek","is_peak","baseline_kwh_per_hour",
                                "tariff_usd_per_kwh","home_size_sqft","occupants"]
                    if c in df.columns]
    categorical_cols = [c for c in CATEGORICAL if c in df.columns]

    X = df[numeric_cols + categorical_cols]
    y = df["kwh_next"].values

    pre = ColumnTransformer([
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
    ], remainder="drop")

    pipe = Pipeline([("pre", pre), ("ridge", Ridge(alpha=0.5))])

    n = len(df)
    split = int(n * 0.8)
    gap = 12
    split_idx = max(0, split - gap)

    X_tr, X_te = X.iloc[:split_idx], X.iloc[split:]
    y_tr, y_te = y[:split_idx], y[split:]

    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    mae  = mean_absolute_error(y_te, pred)
    mape = mean_absolute_percentage_error(y_te, pred)

    print(f"Train rows: {len(X_tr)} | Test rows: {len(X_te)}")
    print(f"Target unique (test): {pd.Series(y_te).nunique()}")
    print(f"MAE={mae:.4f} kWh | MAPE={mape*100:.2f}%")

    Path(MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    print(f"✅ Saved → {MODEL_PATH}")

if __name__ == "__main__":
    main()
