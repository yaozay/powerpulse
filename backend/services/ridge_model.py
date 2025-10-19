from __future__ import annotations

from pathlib import Path
import json
from typing import Iterable, List, Dict, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = "data/alldata.csv"
MODEL_PATH = "data/ridge_pipeline.pkl"
JSON_PATH = "data/output.json"
TS_COL = "timestamp"

NUMERIC_BASE: List[str] = [
    "temp_out_c",
    "humidity",
    "baseline_kwh_per_hour",
    "tariff_usd_per_kwh",
    "home_size_sqft",
    "occupants",
]

CATEGORICAL: List[str] = ["season", "hvac_type", "comfort_level"]


def _resolve(path: str | Path) -> Path:
    return (BASE_DIR / Path(path)).resolve()


def add_time_feats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df[TS_COL].dt.hour
    df["dayofweek"] = df[TS_COL].dt.dayofweek
    df["is_peak"] = df["hour"].between(15, 19).astype(int)
    df["ma3"] = df["kwh"].rolling(3, min_periods=1).mean()
    df["ma12"] = df["kwh"].rolling(12, min_periods=1).mean()
    df["lag1"] = df["kwh"].shift(1)
    df["lag2"] = df["kwh"].shift(2)
    return df


def _select_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, List[str], List[str]]:
    keep_extra = [c for c in NUMERIC_BASE + CATEGORICAL if c in df.columns]
    df = add_time_feats(df)
    cols = [
        TS_COL,
        "kwh",
        "kwh_next",
        "ma3",
        "ma12",
        "lag1",
        "lag2",
        "hour",
        "dayofweek",
        "is_peak",
    ] + keep_extra
    df = df.loc[:, [c for c in cols if c in df.columns]].dropna()

    numeric_cols = [
        c
        for c in [
            "kwh",
            "ma3",
            "ma12",
            "lag1",
            "lag2",
            "temp_out_c",
            "humidity",
            "hour",
            "dayofweek",
            "is_peak",
            "baseline_kwh_per_hour",
            "tariff_usd_per_kwh",
            "home_size_sqft",
            "occupants",
        ]
        if c in df.columns
    ]
    categorical_cols = [c for c in CATEGORICAL if c in df.columns]

    return df, numeric_cols, categorical_cols


def _forecast_future(
    pipe: Pipeline,
    df: pd.DataFrame,
    numeric_cols: Iterable[str],
    categorical_cols: Iterable[str],
    steps: int,
    step: pd.Timedelta,
) -> List[Dict[str, Any]]:
    last = df.iloc[-1].copy()
    k_hist = list(df["kwh"].tail(12).values)
    cur_ts = last[TS_COL]
    out: List[Dict[str, Any]] = []

    for _ in range(steps):
        cur_ts = cur_ts + step
        hour = cur_ts.hour
        dayofweek = cur_ts.dayofweek
        is_peak = int(15 <= hour <= 19)
        lag1 = k_hist[-1] if len(k_hist) >= 1 else last["kwh"]
        lag2 = k_hist[-2] if len(k_hist) >= 2 else lag1
        ma3 = np.mean(k_hist[-3:]) if len(k_hist) >= 3 else np.mean(k_hist) if k_hist else last["kwh"]
        ma12 = np.mean(k_hist[-12:]) if len(k_hist) >= 1 else last["kwh"]

        row_dict: Dict[str, Any] = {
            "kwh": last["kwh"],
            "ma3": ma3,
            "ma12": ma12,
            "lag1": lag1,
            "lag2": lag2,
            "hour": hour,
            "dayofweek": dayofweek,
            "is_peak": is_peak,
        }

        for c in NUMERIC_BASE:
            if c in df.columns:
                row_dict[c] = last[c]
        for c in CATEGORICAL:
            if c in df.columns:
                row_dict[c] = last[c]

        feat_cols = [c for c in list(numeric_cols) + list(categorical_cols) if c in row_dict]
        X_future = pd.DataFrame([{c: row_dict[c] for c in feat_cols}])
        for c in list(numeric_cols) + list(categorical_cols):
            if c not in X_future.columns:
                X_future[c] = np.nan
        X_future = X_future[list(numeric_cols) + list(categorical_cols)]

        kwh_pred = float(pipe.predict(X_future)[0])
        out.append({"timestamp": cur_ts.isoformat(), "predicted_kwh": kwh_pred})

        k_hist.append(kwh_pred)
        if len(k_hist) > 12:
            k_hist = k_hist[-12:]
        last["kwh"] = kwh_pred
        last["hour"] = hour
        last["dayofweek"] = dayofweek
        last["is_peak"] = is_peak

    return out


def train_and_forecast(
    csv_path: str = CSV_PATH,
    model_path: str = MODEL_PATH,
    json_path: str = JSON_PATH,
    forecast_hours: int = 48,
) -> Dict[str, Any]:
    csv_path = _resolve(csv_path)
    model_path = _resolve(model_path)
    json_path = _resolve(json_path)

    df = pd.read_csv(csv_path)
    df[TS_COL] = pd.to_datetime(df[TS_COL], errors="coerce")
    df = df.dropna(subset=[TS_COL, "kwh"]).sort_values(TS_COL)
    df["kwh_next"] = df["kwh"].shift(-1)

    df, numeric_cols, categorical_cols = _select_columns(df)
    if df["kwh_next"].nunique() <= 2:
        raise ValueError(
            "Target still nearly constant after processing. "
            "Check source data or try resampling to 30/60min."
        )

    if not numeric_cols:
        raise ValueError("No numeric columns available after preprocessing.")

    X = df[numeric_cols + categorical_cols]
    y = df["kwh_next"].values

    pre = ColumnTransformer(
        [
            ("num", StandardScaler(), list(numeric_cols)),
            ("cat", OneHotEncoder(handle_unknown="ignore"), list(categorical_cols)),
        ],
        remainder="drop",
    )

    pipe = Pipeline([("pre", pre), ("ridge", Ridge(alpha=0.5))])

    n = len(df)
    split = int(n * 0.8)
    gap = 12
    split_idx = max(0, split - gap)

    X_tr, X_te = X.iloc[:split_idx], X.iloc[split:]
    y_tr, y_te = y[:split_idx], y[split:]
    if len(X_tr) == 0 or len(X_te) == 0:
        raise ValueError("Not enough rows to create a train/test split.")

    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    mae = mean_absolute_error(y_te, pred)
    mape = mean_absolute_percentage_error(y_te, pred)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_path)

    diffs = df[TS_COL].diff().dropna()
    step = diffs.median() if len(diffs) > 0 else pd.Timedelta(hours=1)
    if not isinstance(step, pd.Timedelta):
        step = pd.to_timedelta(step, errors="ignore")  # type: ignore[arg-type]
    if not isinstance(step, pd.Timedelta) or step <= pd.Timedelta(0):
        step = pd.Timedelta(hours=1)

    steps_48h = int(pd.Timedelta(hours=forecast_hours) / step)
    if steps_48h <= 0:
        steps_48h = int(forecast_hours)

    forecast = _forecast_future(pipe, df, numeric_cols, categorical_cols, steps_48h, step)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w") as f:
        json.dump(forecast, f, indent=2)

    return {
        "train_rows": len(X_tr),
        "test_rows": len(X_te),
        "mae": float(mae),
        "mape": float(mape),
        "model_path": str(model_path),
        "json_path": str(json_path),
        "forecast_steps": len(forecast),
    }


def load_forecast(refresh: bool = False, json_path: str = JSON_PATH) -> List[Dict[str, Any]]:
    json_path = _resolve(json_path)
    if refresh or not json_path.exists():
        train_and_forecast(json_path=json_path)
    with json_path.open() as f:
        return json.load(f)


def main() -> None:
    stats = train_and_forecast()
    print(
        f"Train rows: {stats['train_rows']} | Test rows: {stats['test_rows']}\n"
        f"MAE={stats['mae']:.4f} kWh | MAPE={stats['mape']*100:.2f}%\n"
        f"✅ Saved → {stats['model_path']}\n"
        f"Saved 48h JSON forecast → {stats['json_path']} (steps: {stats['forecast_steps']})"
    )


if __name__ == "__main__":
    main()
