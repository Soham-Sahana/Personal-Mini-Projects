"""Streamlit interface for the saved educational classifier."""
import json
import joblib
import streamlit as st
import pandas as pd
from src_utils import ROOT, ARTIFACTS, load_dataset

st.set_page_config(page_title="Breast Cancer Classification", page_icon="🔬", layout="wide")
st.title("Breast Cancer Classification — ML Demonstration")
st.warning("Educational demonstration only. This model is not a medical diagnostic tool and must not guide healthcare decisions.")

model_path = ARTIFACTS / "best_model.joblib"
meta_path = ARTIFACTS / "model_metadata.json"
if not model_path.exists() or not meta_path.exists():
    st.error("Model artifacts are missing. Run `python train.py` first, then restart the app.")
    st.stop()

model = joblib.load(model_path)
metadata = json.loads(meta_path.read_text())
X, y = load_dataset()
features = metadata["feature_names"]

st.write("Enter the 30 numerical feature measurements used by the Wisconsin Diagnostic dataset. For a quick demonstration, load an example record from the bundled public dataset.")
example_choice = st.selectbox("Example record", ["Manual entry"] + [f"Public example #{i}" for i in range(1, 11)])
defaults = {}
if example_choice != "Manual entry":
    idx = int(example_choice.split("#")[1]) - 1
    defaults = X.iloc[idx].to_dict()

with st.form("prediction_form"):
    cols = st.columns(3)
    values = {}
    for i, feature in enumerate(features):
        with cols[i % 3]:
            values[feature] = st.number_input(
                feature, min_value=0.0, value=float(defaults.get(feature, float(X[feature].median()))),
                format="%.6f", key=f"feature_{i}"
            )
    submitted = st.form_submit_button("Run prediction", type="primary")

if submitted:
    row = pd.DataFrame([values], columns=features)
    pred = int(model.predict(row)[0])
    probability = float(model.predict_proba(row)[0, 1])
    label = "Malignant" if pred == 1 else "Benign"
    st.subheader("Model output")
    st.metric("Predicted class", label)
    st.metric("Estimated malignant-class probability", f"{probability:.1%}")
    st.caption("This probability is a model estimate for an educational dataset, not a clinical risk estimate.")
    st.progress(min(max(probability, 0.0), 1.0))
    st.write("Model:", metadata["model_name"])
