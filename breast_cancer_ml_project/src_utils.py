"""Shared data loading and model-building utilities for the assignment."""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

def load_dataset():
    """Load the public Wisconsin Diagnostic dataset distributed by scikit-learn.
    Target is recoded so malignant=1 (positive class), benign=0.
    """
    bunch = load_breast_cancer(as_frame=True)
    X = bunch.data.copy()
    y = (bunch.target == 0).astype(int)  # sklearn original 0=malignant, 1=benign
    y.name = "malignant"
    return X, y

def build_models():
    """All models receive identical imputation/scaling pipeline structure.
    Scaling is important for LR/SVM; tree models are unaffected by scaling.
    Imputation is included inside pipelines to prevent leakage and ease app reuse.
    """
    return {
        "Logistic Regression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=5000, class_weight="balanced", random_state=42))
        ]),
        "Decision Tree": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", DecisionTreeClassifier(class_weight="balanced", random_state=42))
        ]),
        "Random Forest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42, n_jobs=-1))
        ]),
        "Support Vector Machine": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", SVC(probability=True, class_weight="balanced", random_state=42))
        ]),
        "Gradient Boosting": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", GradientBoostingClassifier(random_state=42))
        ]),
    }

def save_model(model, feature_names, model_name):
    path = ARTIFACTS / "best_model.joblib"
    joblib.dump(model, path)
    metadata = {
        "model_name": model_name,
        "feature_names": list(feature_names),
        "target_positive_class": "malignant",
        "target_encoding": {"benign": 0, "malignant": 1},
        "disclaimer": "Educational model only; not a medical diagnostic tool."
    }
    (ARTIFACTS / "model_metadata.json").write_text(json.dumps(metadata, indent=2))
    return path
