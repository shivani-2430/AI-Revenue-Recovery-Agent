from pathlib import Path
import json
import pickle

import pandas as pd

try:
    import joblib
except ImportError:
    joblib = None

from models.policy import Policy


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

    if joblib is not None:
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            pass

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


def _get_model_name(
    metrics,
    model,
):
    model_name = metrics.get("model")

    if isinstance(
        model_name,
        dict,
    ):
        model_name = model_name.get("name")

    if model_name:
        return str(model_name)

    if model is None:
        return "Recovery Intelligence"

    return type(model).__name__


def _get_features(
    metrics,
    model,
):
    features = metrics.get("features")

    if isinstance(
        features,
        list,
    ) and features:

        return [
            str(feature)
            for feature in features
        ]

    if isinstance(
        features,
        dict,
    ):

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

    return []


def _get_performance(metrics):
    """
    model_metrics.json stores performance
    metrics at the top level.
    """

    return {
        "accuracy": metrics.get(
            "accuracy"
        ),
        "precision": metrics.get(
            "precision"
        ),
        "recall": metrics.get(
            "recall"
        ),
        "f1_score": metrics.get(
            "f1_score"
        ),
        "roc_auc": metrics.get(
            "roc_auc"
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
        isinstance(
            distribution,
            dict,
        )
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
    """
    Prefer feature importance metadata only when
    it is already supplied by the metrics file.

    Otherwise derive importance from the model.

    If the model contains transformed/encoded
    features that cannot be mapped reliably to the
    original business feature names, expose the
    transformed feature names instead of falsely
    assigning them to unrelated business fields.
    """

    importance = metrics.get(
        "feature_importance",
        [],
    )

    if (
        isinstance(
            importance,
            list,
        )
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

    transformed_features = []

    try:
        if hasattr(
            model,
            "get_feature_names_out",
        ):

            transformed_features = list(
                model.get_feature_names_out()
            )

    except Exception:
        transformed_features = []

    features = transformed_features

    if not features:

        try:
            if hasattr(
                estimator,
                "feature_names_in_",
            ):

                features = [
                    str(feature)
                    for feature
                    in estimator.feature_names_in_
                ]

        except Exception:
            features = []

    result = []

    for index, value in enumerate(values):

        if index < len(features):

            feature_name = features[index]

        else:

            feature_name = (
                f"Encoded Feature {index + 1}"
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


def _get_threshold_policy():
    """
    Load the active recovery decision policy
    from PostgreSQL.

    Model Intelligence should reflect the actual
    RecoverAI policy configuration instead of
    inventing a threshold from model metadata.
    """

    try:

        policy = (
            Policy.query
            .order_by(
                Policy.id.asc()
            )
            .first()
        )

    except Exception:
        return {}

    if policy is None:
        return {}

    minimum_probability = float(
        policy.minimum_recovery_probability
    )

    escalation_threshold = float(
        policy.escalation_threshold
    )

    maximum_retry_count = int(
        policy.maximum_retry_count
    )

    return {
        "title": (
            f"Recovery threshold: "
            f"{minimum_probability:.0f}%"
        ),

        "threshold": minimum_probability,

        "description": (
            f"Recovery opportunities with an "
            f"estimated recovery probability of "
            f"{minimum_probability:.0f}% or higher "
            f"can proceed through recovery guardrails. "
            f"Probabilities at or above "
            f"{escalation_threshold:.0f}% may receive "
            f"priority handling. Maximum retries: "
            f"{maximum_retry_count}."
        ),

        "minimum_recovery_probability":
            minimum_probability,

        "escalation_threshold":
            escalation_threshold,

        "maximum_retry_count":
            maximum_retry_count,
    }


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
        model
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
        _get_threshold_policy()
    )

    model_name = _get_model_name(
        metrics,
        model,
    )

    model_version = metrics.get(
        "version",
        "v1",
    )

    prediction_target = (
        "Recovery Probability"
    )

    dataset_name = (
        DATASET_PATH.name
    )

    description = (
        "Machine learning model used "
        "to estimate payment recovery "
        "potential."
    )

    metrics_available = any(
        value is not None
        for key, value
        in performance.items()
        if key != "accuracy"
    )

    return {
        "model": {
            "name": model_name,
            "version": model_version,
            "target": prediction_target,
            "dataset": dataset_name,
            "description": description,
            "model_file": MODEL_PATH.name,
            "model_available": (
                model is not None
            ),
        },

        "performance": performance,

        "features": features,

        "confusion_matrix":
            confusion_matrix,

        "class_distribution":
            class_distribution,

        "feature_importance":
            feature_importance,

        "threshold_policy":
            threshold_policy,

        "metrics_available":
            metrics_available,
    }