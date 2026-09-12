from pathlib import Path
import json
import pickle

import pandas as pd

try:
    import joblib
except ImportError:
    joblib = None


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "ml" / "recovery_model.pkl"
METRICS_PATH = BASE_DIR / "ml" / "model_metrics.json"
DATASET_PATH = BASE_DIR / "ml" / "recovery_dataset.csv"


def _load_json_file(path):
    if not path.exists():
        return {}

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}


def _load_model():
    if not MODEL_PATH.exists():
        return None

    # Try joblib first because sklearn models are commonly
    # saved with joblib.dump().
    if joblib is not None:
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            pass

    # Fallback to standard pickle.
    try:
        with MODEL_PATH.open("rb") as file:
            return pickle.load(file)
    except Exception:
        return None


def _load_dataset():
    if not DATASET_PATH.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(DATASET_PATH)
    except Exception:
        return pd.DataFrame()


def _get_model_name(model):
    if model is None:
        return "Recovery Intelligence"

    model_name = type(model).__name__

    if hasattr(model, "named_steps"):
        try:
            steps = list(model.named_steps.keys())

            if steps:
                final_step = model.named_steps[steps[-1]]
                model_name = type(final_step).__name__
        except Exception:
            pass

    return model_name


def _get_features(metrics, model):
    features = metrics.get("features")

    if isinstance(features, list) and features:
        return [
            str(feature)
            for feature in features
        ]

    if isinstance(features, dict):
        return [
            str(feature)
            for feature in features.keys()
        ]

    if model is not None:

        try:
            if hasattr(
                model,
                "feature_names_in_",
            ):
                return [
                    str(feature)
                    for feature in model.feature_names_in_
                ]
        except Exception:
            pass

        try:
            if hasattr(
                model,
                "named_steps",
            ):
                for step in model.named_steps.values():

                    if hasattr(
                        step,
                        "feature_names_in_",
                    ):
                        return [
                            str(feature)
                            for feature in step.feature_names_in_
                        ]
        except Exception:
            pass

    return []


def _get_performance(metrics):
    performance = metrics.get(
        "performance",
        {},
    )

    if not isinstance(
        performance,
        dict,
    ):
        return {}

    return {
        "precision": performance.get(
            "precision"
        ),
        "recall": performance.get(
            "recall"
        ),
        "f1_score": performance.get(
            "f1_score",
            performance.get("f1"),
        ),
        "roc_auc": performance.get(
            "roc_auc",
            performance.get(
                "roc_auc_score"
            ),
        ),
    }


def _get_class_distribution(
    metrics,
    dataset,
):
    distribution = metrics.get(
        "class_distribution",
        {},
    )

    if (
        isinstance(distribution, dict)
        and distribution
    ):
        return distribution

    if dataset.empty:
        return {}

    if "recovery_possible" not in dataset.columns:
        return {}

    try:
        values = (
            dataset[
                "recovery_possible"
            ]
            .value_counts(
                dropna=False
            )
            .to_dict()
        )
    except Exception:
        return {}

    result = {}

    for key, value in values.items():
        result[str(key)] = int(value)

    return result


def _get_confusion_matrix(metrics):
    matrix = metrics.get(
        "confusion_matrix",
        {},
    )

    if isinstance(
        matrix,
        dict,
    ):
        return matrix

    if isinstance(
        matrix,
        list,
    ):
        return {
            "matrix": matrix,
        }

    return {}


def _get_feature_importance(
    metrics,
    model,
):
    importance = metrics.get(
        "feature_importance",
        [],
    )

    if (
        isinstance(importance, list)
        and importance
    ):
        return importance

    if model is None:
        return []

    estimator = model

    try:
        if hasattr(
            model,
            "named_steps",
        ):
            steps = list(
                model.named_steps.values()
            )

            if steps:
                estimator = steps[-1]
    except Exception:
        return []

    if not hasattr(
        estimator,
        "feature_importances_",
    ):
        return []

    try:
        values = (
            estimator.feature_importances_
        )
    except Exception:
        return []

    features = _get_features(
        metrics,
        model,
    )

    result = []

    for index, value in enumerate(values):

        if index < len(features):
            feature_name = features[index]
        else:
            feature_name = (
                f"Feature {index + 1}"
            )

        result.append(
            {
                "feature": str(
                    feature_name
                ),
                "importance": float(
                    value
                ),
            }
        )

    result.sort(
        key=lambda item:
            item["importance"],
        reverse=True,
    )

    return result


def _get_threshold_policy(metrics):
    policy = metrics.get(
        "threshold_policy",
        {},
    )

    if isinstance(
        policy,
        dict,
    ):
        return policy

    return {}


def get_model_intelligence():

    metrics = _load_json_file(
        METRICS_PATH
    )

    model = _load_model()

    dataset = _load_dataset()

    performance = _get_performance(
        metrics
    )

    features = _get_features(
        metrics,
        model,
    )

    class_distribution = (
        _get_class_distribution(
            metrics,
            dataset,
        )
    )

    confusion_matrix = (
        _get_confusion_matrix(
            metrics
        )
    )

    feature_importance = (
        _get_feature_importance(
            metrics,
            model,
        )
    )

    threshold_policy = (
        _get_threshold_policy(
            metrics
        )
    )

    model_metadata = metrics.get(
        "model",
        {},
    )

    if not isinstance(
        model_metadata,
        dict,
    ):
        model_metadata = {}

    model_name = model_metadata.get(
        "name"
    )

    if not model_name:
        model_name = _get_model_name(
            model
        )

    model_version = (
        model_metadata.get(
            "version",
            "v1",
        )
    )

    prediction_target = (
        model_metadata.get(
            "target",
            "Recovery Probability",
        )
    )

    dataset_name = (
        model_metadata.get(
            "dataset",
            DATASET_PATH.name,
        )
    )

    description = (
        model_metadata.get(
            "description",
            (
                "Machine learning model used "
                "to estimate payment recovery "
                "potential."
            ),
        )
    )

    return {
        "model": {
            "name": model_name,
            "version": model_version,
            "target": prediction_target,
            "dataset": dataset_name,
            "description": description,
            "model_file": MODEL_PATH.name,
            "model_available": model is not None,
        },
        "performance": performance,
        "features": features,
        "confusion_matrix": confusion_matrix,
        "class_distribution": class_distribution,
        "feature_importance": feature_importance,
        "threshold_policy": threshold_policy,
        "metrics_available": bool(
            performance
        ),
    }