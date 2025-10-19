import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from .features import NUMERIC_FEATURES, CATEGORICAL_FEATURES

_MODEL = {"pipe": None, "path": None}

def load_pipeline(path: str):
    if _MODEL["pipe"] is None or _MODEL["path"] != path:
        _MODEL["pipe"] = joblib.load(path)
        _MODEL["path"] = path
    return _MODEL["pipe"]

def predict_batch(rows: List[Dict[str, Any]], model_path: str) -> list[float]:
    pipe = load_pipeline(model_path)
    X = pd.DataFrame(rows)
    cols = [c for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES if c in X.columns]
    return pipe.predict(X[cols]).tolist()
