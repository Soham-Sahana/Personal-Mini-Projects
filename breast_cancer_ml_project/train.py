"""Run EDA, train and compare classifiers, tune the best baseline, and save artifacts."""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, ConfusionMatrixDisplay, RocCurveDisplay, classification_report
)
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from src_utils import ROOT, ARTIFACTS, load_dataset, build_models, save_model

warnings.filterwarnings("ignore", category=UserWarning)
sns.set_theme(style="whitegrid")
PLOTS = ROOT / "plots"
PLOTS.mkdir(exist_ok=True)
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

def main():
    X, y = load_dataset()
    df = X.copy()
    df["diagnosis_malignant"] = y
    # Data quality / summary outputs
    (RESULTS / "dataset_overview.txt").write_text(
        f"Rows: {len(df)}\nPredictor features: {X.shape[1]}\nTarget: diagnosis_malignant (1=malignant, 0=benign)\n"
        f"Missing cells: {int(df.isna().sum().sum())}\nDuplicate rows: {int(df.duplicated().sum())}\n\n"
        f"Target counts:\n{y.value_counts().rename(index={0:'benign',1:'malignant'}).to_string()}\n\n"
        f"Descriptive statistics:\n{X.describe().T.to_string()}\n"
    )
    df.head(10).to_csv(RESULTS / "sample_rows.csv", index=False)
    df.describe().T.to_csv(RESULTS / "descriptive_statistics.csv")
    df.isna().sum().rename("missing_count").to_csv(RESULTS / "missing_values.csv")

    # EDA plots
    plt.figure(figsize=(6,4))
    y.map({0:"Benign",1:"Malignant"}).value_counts().reindex(["Benign","Malignant"]).plot(kind="bar")
    plt.title("Target Class Distribution"); plt.xlabel("Diagnosis"); plt.ylabel("Samples")
    plt.tight_layout(); plt.savefig(PLOTS / "class_distribution.png", dpi=160); plt.close()

    # Histograms for representative features
    sample_features = ["mean radius", "mean texture", "mean perimeter", "mean area",
                       "mean smoothness", "mean concavity"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, feature in zip(axes.flat, sample_features):
        sns.histplot(data=df, x=feature, hue="diagnosis_malignant", bins=25,
                     stat="density", common_norm=False, element="step", ax=ax)
        ax.set_title(feature)
    fig.suptitle("Selected Feature Distributions by Diagnosis")
    fig.tight_layout(); fig.savefig(PLOTS / "feature_distributions.png", dpi=160); plt.close(fig)

    plt.figure(figsize=(15,12))
    corr = X.corr(numeric_only=True)
    sns.heatmap(corr, cmap="coolwarm", center=0, xticklabels=False, yticklabels=False)
    plt.title("Correlation Heatmap of 30 Features")
    plt.tight_layout(); plt.savefig(PLOTS / "correlation_heatmap.png", dpi=160); plt.close()

    plt.figure(figsize=(10,6))
    sns.boxplot(data=df[["mean radius","mean texture","mean perimeter","mean area","mean concavity"]])
    plt.xticks(rotation=25, ha="right"); plt.title("Boxplots of Selected Features")
    plt.tight_layout(); plt.savefig(PLOTS / "selected_feature_boxplots.png", dpi=160); plt.close()

    # Stratified split. Test set remains untouched during model selection/tuning.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    models = build_models()
    rows, fitted = [], {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1]
        rows.append({
            "Model": name,
            "Accuracy": accuracy_score(y_test, pred),
            "Precision": precision_score(y_test, pred, zero_division=0),
            "Recall": recall_score(y_test, pred, zero_division=0),
            "F1": f1_score(y_test, pred, zero_division=0),
            "ROC_AUC": roc_auc_score(y_test, proba)
        })
        fitted[name] = model
        cm = confusion_matrix(y_test, pred, labels=[0,1])
        disp = ConfusionMatrixDisplay(cm, display_labels=["Benign","Malignant"])
        disp.plot(cmap="Blues", values_format="d")
        plt.title(f"Confusion Matrix — {name}")
        plt.tight_layout()
        plt.savefig(PLOTS / f"confusion_matrix_{name.lower().replace(' ','_')}.png", dpi=160)
        plt.close()

    baseline = pd.DataFrame(rows).sort_values("ROC_AUC", ascending=False)
    baseline.to_csv(RESULTS / "baseline_model_comparison.csv", index=False)

    # Comparison charts
    metrics = ["Accuracy","Precision","Recall","F1","ROC_AUC"]
    baseline.set_index("Model")[metrics].plot(kind="bar", figsize=(12,6), ylim=(0,1.02))
    plt.ylabel("Score"); plt.title("Baseline Model Comparison"); plt.xticks(rotation=25, ha="right")
    plt.tight_layout(); plt.savefig(PLOTS / "model_comparison.png", dpi=160); plt.close()

    plt.figure(figsize=(8,7))
    for name, model in fitted.items():
        RocCurveDisplay.from_estimator(model, X_test, y_test, name=name, ax=plt.gca())
    plt.plot([0,1],[0,1],"k--", linewidth=1)
    plt.title("ROC Curves on Held-Out Test Set")
    plt.tight_layout(); plt.savefig(PLOTS / "roc_curves.png", dpi=160); plt.close()

    # Tune the best baseline by ROC-AUC using CV on training data only.
    best_name = baseline.iloc[0]["Model"]
    best_pipe = fitted[best_name]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    if best_name == "Logistic Regression":
        param_grid = {"model__C":[0.01,0.1,1,10], "model__solver":["liblinear","lbfgs"]}
    elif best_name == "Decision Tree":
        param_grid = {"model__max_depth":[None,3,5,8], "model__min_samples_leaf":[1,2,4]}
    elif best_name == "Random Forest":
        param_grid = {"model__n_estimators":[200,400], "model__max_depth":[None,5,10],
                      "model__min_samples_leaf":[1,2]}
    elif best_name == "Support Vector Machine":
        param_grid = {"model__C":[0.1,1,10], "model__kernel":["rbf","linear"],
                      "model__gamma":["scale","auto"]}
    else:
        param_grid = {"model__n_estimators":[100,200], "model__learning_rate":[0.03,0.1],
                      "model__max_depth":[1,2,3]}
    search = GridSearchCV(best_pipe, param_grid, scoring="roc_auc", cv=cv, n_jobs=-1, refit=True)
    search.fit(X_train, y_train)
    tuned = search.best_estimator_
    pred = tuned.predict(X_test)
    proba = tuned.predict_proba(X_test)[:,1]
    tuned_row = {
        "Model": f"{best_name} (tuned)",
        "Accuracy": accuracy_score(y_test,pred),
        "Precision": precision_score(y_test,pred,zero_division=0),
        "Recall": recall_score(y_test,pred,zero_division=0),
        "F1": f1_score(y_test,pred,zero_division=0),
        "ROC_AUC": roc_auc_score(y_test,proba)
    }
    tuned_df = pd.DataFrame([tuned_row])
    tuned_df.to_csv(RESULTS / "tuned_model_comparison.csv", index=False)
    combined = pd.concat([baseline, tuned_df], ignore_index=True)
    combined.to_csv(RESULTS / "all_model_comparison.csv", index=False)
    with open(RESULTS / "tuning_summary.json","w") as f:
        json.dump({"baseline_best_model":best_name, "best_params":search.best_params_,
                   "best_cv_roc_auc":float(search.best_score_),
                   "tuned_test_metrics":tuned_row}, f, indent=2)

    save_model(tuned, X.columns, f"{best_name} (tuned)")
    (RESULTS / "best_model_classification_report.txt").write_text(
        classification_report(y_test, pred, target_names=["Benign","Malignant"], zero_division=0)
    )
    # Save split-independent feature reference and experiment setup
    (RESULTS / "experiment_setup.txt").write_text(
        "Dataset: Breast Cancer Wisconsin (Diagnostic), loaded using sklearn.datasets.load_breast_cancer\n"
        "Rows=569; predictor features=30; target=malignant (1) vs benign (0)\n"
        "Split: 80% train / 20% test, stratified, random_state=42\n"
        "Baseline models share the same held-out split; all preprocessing occurs inside sklearn pipelines.\n"
        "Tuning: GridSearchCV with 5-fold StratifiedKFold on training set only; test set used for final evaluation.\n"
        "Positive class for precision/recall/F1/ROC-AUC: malignant (1).\n"
    )
    print("\nBASELINE MODEL COMPARISON")
    print(baseline.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nTUNED MODEL")
    print(pd.DataFrame([tuned_row]).to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nBest baseline:", best_name)
    print("Best parameters:", search.best_params_)
    print("Best CV ROC-AUC:", round(search.best_score_, 4))
    print("\nArtifacts saved under:", ROOT)

if __name__ == "__main__":
    main()
