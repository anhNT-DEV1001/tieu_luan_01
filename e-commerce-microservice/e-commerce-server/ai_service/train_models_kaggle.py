import argparse
import json
import os
import pickle
from pathlib import Path
from typing import Optional

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import FeatureUnion
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
DEFAULT_DATASET_PATH = DATA_DIR / "intent_seed_dataset.csv"
MODEL_PATH = MODELS_DIR / "chatbot_intent_model.pkl"
VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.pkl"
METADATA_PATH = MODELS_DIR / "training_metadata.json"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

TEXT_COLUMN_CANDIDATES = ("text", "sentence", "utterance", "query", "message", "instruction")
LABEL_COLUMN_CANDIDATES = ("intent", "label", "category", "class", "target")
SUPPORTED_INTENTS = {
    "greeting",
    "product_inquiry",
    "order_status",
    "complaint",
    "farewell",
    "customer_lookup",
    "unknown",
}
LABEL_ALIASES = {
    "greeting": "greeting",
    "hello": "greeting",
    "welcome": "greeting",
    "product_inquiry": "product_inquiry",
    "product": "product_inquiry",
    "catalog": "product_inquiry",
    "browse_products": "product_inquiry",
    "order_status": "order_status",
    "track_order": "order_status",
    "shipping_status": "order_status",
    "order_tracking": "order_status",
    "complaint": "complaint",
    "support_ticket": "complaint",
    "issue": "complaint",
    "refund": "complaint",
    "farewell": "farewell",
    "goodbye": "farewell",
    "customer_lookup": "customer_lookup",
    "customer": "customer_lookup",
    "user_lookup": "customer_lookup",
    "unknown": "unknown",
    "other": "unknown",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train chatbot intent model using local or Kaggle dataset.")
    parser.add_argument("--dataset", default=os.getenv("KAGGLE_DATASET_PATH", str(DEFAULT_DATASET_PATH)))
    parser.add_argument("--text-column", default=os.getenv("KAGGLE_TEXT_COLUMN"))
    parser.add_argument("--label-column", default=os.getenv("KAGGLE_LABEL_COLUMN"))
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def detect_column(columns: list[str], explicit: Optional[str], candidates: tuple[str, ...], column_type: str) -> str:
    if explicit:
        if explicit not in columns:
            raise ValueError(f"{column_type} column '{explicit}' not found in dataset columns: {columns}")
        return explicit

    lowered = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]

    raise ValueError(f"Could not detect {column_type} column. Available columns: {columns}")


def load_dataset(dataset_path: Path, text_column: Optional[str], label_column: Optional[str]) -> pd.DataFrame:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    suffix = dataset_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(dataset_path)
    elif suffix in {".json", ".jsonl"}:
        df = pd.read_json(dataset_path, lines=suffix == ".jsonl")
    else:
        raise ValueError(f"Unsupported dataset format '{suffix}'. Use CSV, JSON, or JSONL.")

    if df.empty:
        raise ValueError("Dataset is empty.")

    resolved_text_column = detect_column(df.columns.tolist(), text_column, TEXT_COLUMN_CANDIDATES, "text")
    resolved_label_column = detect_column(df.columns.tolist(), label_column, LABEL_COLUMN_CANDIDATES, "label")
    normalized = df[[resolved_text_column, resolved_label_column]].rename(
        columns={resolved_text_column: "text", resolved_label_column: "intent"}
    )
    normalized["text"] = normalized["text"].astype(str).str.strip()
    normalized["intent"] = normalized["intent"].astype(str).str.strip().str.lower()
    normalized = normalized[(normalized["text"] != "") & (normalized["intent"] != "")]
    return normalized


def canonicalize_label(raw_label: str) -> str:
    normalized = raw_label.strip().lower().replace(" ", "_")
    return LABEL_ALIASES.get(normalized, normalized if normalized in SUPPORTED_INTENTS else "unknown")


def enrich_dataset(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["intent"] = enriched["intent"].map(canonicalize_label)
    enriched["text"] = enriched["text"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    enriched = enriched[(enriched["text"] != "") & (enriched["intent"] != "")]
    return enriched.drop_duplicates(subset=["text", "intent"]).reset_index(drop=True)


def build_vectorizer() -> FeatureUnion:
    return FeatureUnion(
        [
            (
                "word_tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.98,
                    sublinear_tf=True,
                    max_features=6000,
                ),
            ),
            (
                "char_tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=1,
                    max_df=0.98,
                    sublinear_tf=True,
                    max_features=8000,
                ),
            ),
        ]
    )


def train_model(df: pd.DataFrame, test_size: float, random_state: int):
    if df["intent"].nunique() < 2:
        raise ValueError("Need at least 2 intents to train the model.")

    has_enough_data_for_split = df["intent"].value_counts().min() >= 2 and len(df) >= 10
    if has_enough_data_for_split:
        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=df["intent"],
        )
    else:
        train_df = df
        test_df = df.copy()

    vectorizer = build_vectorizer()
    X_train = vectorizer.fit_transform(train_df["text"])
    y_train = train_df["intent"]

    model = LogisticRegression(
        random_state=random_state,
        max_iter=2000,
        class_weight="balanced",
        multi_class="auto",
        solver="lbfgs",
    )
    model.fit(X_train, y_train)

    X_test = vectorizer.transform(test_df["text"])
    y_test = test_df["intent"]
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    return model, vectorizer, accuracy, report, train_df, test_df


def save_artifacts(model, vectorizer, metadata: dict) -> None:
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(model, model_file)
    with VECTORIZER_PATH.open("wb") as vectorizer_file:
        pickle.dump(vectorizer, vectorizer_file)
    with METADATA_PATH.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset).resolve()
    print(f"Loading dataset from: {dataset_path}")
    raw_df = load_dataset(dataset_path, args.text_column, args.label_column)
    df = enrich_dataset(raw_df)

    print("Intent distribution:")
    print(df["intent"].value_counts().sort_index().to_string())

    model, vectorizer, accuracy, report, train_df, test_df = train_model(
        df=df,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    metadata = {
        "dataset_path": str(dataset_path),
        "row_count": int(len(df)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "intents": sorted(df["intent"].unique().tolist()),
        "accuracy": round(float(accuracy), 4),
        "classification_report": report,
    }
    save_artifacts(model, vectorizer, metadata)

    print(f"Training accuracy: {accuracy * 100:.2f}%")
    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved vectorizer to: {VECTORIZER_PATH}")
    print(f"Saved metadata to: {METADATA_PATH}")


if __name__ == "__main__":
    main()
