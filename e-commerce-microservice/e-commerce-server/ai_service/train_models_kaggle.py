import argparse
import json
import os
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from openai import OpenAI
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
DEFAULT_DATASET_PATH = DATA_DIR / "intent_seed_dataset.csv"
TRAIN_JSONL_PATH = MODELS_DIR / "fine_tune_train.jsonl"
VALID_JSONL_PATH = MODELS_DIR / "fine_tune_valid.jsonl"
METADATA_PATH = MODELS_DIR / "training_metadata.json"
LOCAL_MODEL_PATH = MODELS_DIR / "intent_mlp_model.npz"

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
INTENT_REPLY_TEMPLATES = {
    "greeting": "Chao ban! Minh co the ho tro tim san pham, don hang hoac thong tin khach hang.",
    "product_inquiry": "Minh se ho tro tra cuu san pham. Neu co the, hay cung cap them ten san pham, SKU hoac danh muc.",
    "order_status": "Minh se ho tro kiem tra don hang. Hay gui ma don hang neu ban co.",
    "complaint": "Minh rat tiec ve trai nghiem nay. Hay cho minh biet them chi tiet de minh ho tro dung huong.",
    "farewell": "Tam biet! Neu can ho tro them, ban cu nhan tiep nhe.",
    "customer_lookup": "Minh se ho tro tra cuu thong tin khach hang. Email, so dien thoai hoac ma khach hang se rat huu ich.",
    "unknown": "Minh chua hieu ro yeu cau. Ban co the dien dat cu the hon khong?",
}
CLASSIFIER_DEVELOPER_PROMPT = (
    "You are an e-commerce assistant intent classifier. "
    "Return valid JSON with keys intent, answer, confidence. "
    "intent must be one of: greeting, product_inquiry, order_status, complaint, farewell, customer_lookup, unknown. "
    "answer must be a short helpful Vietnamese response. "
    "confidence must be a number from 0 to 1."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a local neural intent classifier and prepare optional OpenAI fine-tuning data.")
    parser.add_argument("--dataset", default=os.getenv("KAGGLE_DATASET_PATH", str(DEFAULT_DATASET_PATH)))
    parser.add_argument("--text-column", default=os.getenv("KAGGLE_TEXT_COLUMN"))
    parser.add_argument("--label-column", default=os.getenv("KAGGLE_LABEL_COLUMN"))
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--max-features", type=int, default=int(os.getenv("INTENT_MAX_FEATURES", "2000")))
    parser.add_argument("--hidden-size", type=int, default=int(os.getenv("INTENT_HIDDEN_SIZE", "128")))
    parser.add_argument("--hidden-size-2", type=int, default=int(os.getenv("INTENT_HIDDEN_SIZE_2", "64")))
    parser.add_argument("--epochs", type=int, default=int(os.getenv("INTENT_EPOCHS", "1200")))
    parser.add_argument("--learning-rate", type=float, default=float(os.getenv("INTENT_LEARNING_RATE", "0.003")))
    parser.add_argument("--weight-decay", type=float, default=float(os.getenv("INTENT_WEIGHT_DECAY", "0.0001")))
    parser.add_argument("--base-model", default=os.getenv("OPENAI_FINE_TUNE_BASE_MODEL", "gpt-4.1-mini-2025-04-14"))
    parser.add_argument("--suffix", default=os.getenv("OPENAI_FINE_TUNE_SUFFIX", "ecommerce-assistant"))
    parser.add_argument("--create-job", action="store_true")
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


def build_fine_tune_record(text: str, intent: str) -> dict:
    answer = INTENT_REPLY_TEMPLATES.get(intent, INTENT_REPLY_TEMPLATES["unknown"])
    assistant_payload = {
        "intent": intent,
        "answer": answer,
        "confidence": 0.95,
    }
    return {
        "messages": [
            {"role": "developer", "content": CLASSIFIER_DEVELOPER_PROMPT},
            {"role": "user", "content": text},
            {"role": "assistant", "content": json.dumps(assistant_payload, ensure_ascii=True)},
        ]
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=True) + "\n")


def maybe_split_dataset(df: pd.DataFrame, test_size: float, random_state: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    can_stratify = df["intent"].value_counts().min() >= 2 and len(df) >= 10
    if can_stratify:
        train_df, valid_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=df["intent"],
        )
    else:
        train_df = df
        valid_df = df.iloc[:0].copy()
    return train_df.reset_index(drop=True), valid_df.reset_index(drop=True)


def tokenize(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", str(text).strip().lower())
    words = re.findall(r"[\wÀ-ỹ]+", normalized, flags=re.UNICODE)
    features: list[str] = []

    for word in words:
        features.append(f"w:{word}")

    for first, second in zip(words, words[1:]):
        features.append(f"b:{first}_{second}")

    compact = normalized.replace(" ", "_")
    for size in (3, 4):
        if len(compact) >= size:
            features.extend(f"c:{compact[index:index + size]}" for index in range(len(compact) - size + 1))

    return features


def build_vocab(texts: list[str], max_features: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for text in texts:
        for token in tokenize(text):
            counts[token] = counts.get(token, 0) + 1

    ordered_tokens = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:max_features]
    return {token: index for index, (token, _) in enumerate(ordered_tokens)}


def vectorize_texts(texts: list[str], vocab: dict[str, int]) -> np.ndarray:
    matrix = np.zeros((len(texts), len(vocab)), dtype=np.float32)
    for row_index, text in enumerate(texts):
        tokens = tokenize(text)
        if not tokens:
            continue
        for token in tokens:
            column_index = vocab.get(token)
            if column_index is not None:
                matrix[row_index, column_index] = 1.0
    return matrix


def one_hot(labels: np.ndarray, class_count: int) -> np.ndarray:
    encoded = np.zeros((labels.shape[0], class_count), dtype=np.float32)
    encoded[np.arange(labels.shape[0]), labels] = 1.0
    return encoded


def relu(values: np.ndarray) -> np.ndarray:
    return np.maximum(values, 0.0)


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp_values = np.exp(shifted)
    return exp_values / exp_values.sum(axis=1, keepdims=True)


def train_mlp(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    max_features: int,
    hidden_size: int,
    hidden_size_2: int,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    random_state: int,
) -> dict:
    rng = np.random.default_rng(random_state)
    labels = sorted(train_df["intent"].unique().tolist())
    label_to_index = {label: index for index, label in enumerate(labels)}
    vocab = build_vocab(train_df["text"].tolist(), max_features=max_features)

    x_train = vectorize_texts(train_df["text"].tolist(), vocab)
    y_train = np.array([label_to_index[label] for label in train_df["intent"]], dtype=np.int64)
    y_train_oh = one_hot(y_train, len(labels))

    input_size = max(1, x_train.shape[1])
    w1 = rng.normal(0, np.sqrt(2.0 / input_size), size=(input_size, hidden_size)).astype(np.float32)
    b1 = np.zeros((1, hidden_size), dtype=np.float32)
    w2 = rng.normal(0, np.sqrt(2.0 / hidden_size), size=(hidden_size, hidden_size_2)).astype(np.float32)
    b2 = np.zeros((1, hidden_size_2), dtype=np.float32)
    w3 = rng.normal(0, np.sqrt(2.0 / hidden_size_2), size=(hidden_size_2, len(labels))).astype(np.float32)
    b3 = np.zeros((1, len(labels)), dtype=np.float32)
    parameters = [w1, b1, w2, b2, w3, b3]
    first_moments = [np.zeros_like(parameter) for parameter in parameters]
    second_moments = [np.zeros_like(parameter) for parameter in parameters]
    beta1 = 0.9
    beta2 = 0.999
    epsilon = 1e-8

    for epoch in range(1, max(1, epochs) + 1):
        z1 = x_train @ w1 + b1
        a1 = relu(z1)
        z2 = a1 @ w2 + b2
        a2 = relu(z2)
        logits = a2 @ w3 + b3
        probabilities = softmax(logits)

        dlogits = (probabilities - y_train_oh) / max(1, x_train.shape[0])
        dw3 = a2.T @ dlogits + weight_decay * w3
        db3 = dlogits.sum(axis=0, keepdims=True)
        da2 = dlogits @ w3.T
        dz2 = da2 * (z2 > 0)
        dw2 = a1.T @ dz2 + weight_decay * w2
        db2 = dz2.sum(axis=0, keepdims=True)
        da1 = dz2 @ w2.T
        dz1 = da1 * (z1 > 0)
        dw1 = x_train.T @ dz1 + weight_decay * w1
        db1 = dz1.sum(axis=0, keepdims=True)

        gradients = [dw1, db1, dw2, db2, dw3, db3]
        for index, (parameter, gradient) in enumerate(zip(parameters, gradients)):
            first_moments[index] = beta1 * first_moments[index] + (1 - beta1) * gradient
            second_moments[index] = beta2 * second_moments[index] + (1 - beta2) * np.square(gradient)
            first_unbiased = first_moments[index] / (1 - beta1**epoch)
            second_unbiased = second_moments[index] / (1 - beta2**epoch)
            parameter -= learning_rate * first_unbiased / (np.sqrt(second_unbiased) + epsilon)

    train_predictions = predict_with_weights(x_train, w1, b1, w2, b2, w3, b3)
    train_accuracy = float((train_predictions == y_train).mean()) if len(y_train) else 0.0

    validation_accuracy = None
    report = None
    if not valid_df.empty:
        x_valid = vectorize_texts(valid_df["text"].tolist(), vocab)
        y_valid = np.array([label_to_index.get(label, -1) for label in valid_df["intent"]], dtype=np.int64)
        valid_mask = y_valid >= 0
        if valid_mask.any():
            valid_predictions = predict_with_weights(x_valid[valid_mask], w1, b1, w2, b2, w3, b3)
            validation_accuracy = float((valid_predictions == y_valid[valid_mask]).mean())
            report = classification_report(
                y_valid[valid_mask],
                valid_predictions,
                target_names=labels,
                labels=list(range(len(labels))),
                output_dict=True,
                zero_division=0,
            )

    np.savez_compressed(
        LOCAL_MODEL_PATH,
        w1=w1,
        b1=b1,
        w2=w2,
        b2=b2,
        w3=w3,
        b3=b3,
        vocab=np.array(json.dumps(vocab, ensure_ascii=False)),
        labels=np.array(json.dumps(labels, ensure_ascii=False)),
    )

    return {
        "model_path": str(LOCAL_MODEL_PATH),
        "model_type": "numpy_mlp_text_classifier",
        "architecture": {
            "input_features": int(len(vocab)),
            "hidden_layers": [int(hidden_size), int(hidden_size_2)],
            "activation": "relu",
            "output": "softmax",
        },
        "train_accuracy": round(train_accuracy, 4),
        "validation_accuracy": round(validation_accuracy, 4) if validation_accuracy is not None else None,
        "classification_report": report,
        "labels": labels,
    }


def predict_with_weights(
    features: np.ndarray,
    w1: np.ndarray,
    b1: np.ndarray,
    w2: np.ndarray,
    b2: np.ndarray,
    w3: np.ndarray,
    b3: np.ndarray,
) -> np.ndarray:
    hidden = relu(features @ w1 + b1)
    hidden_2 = relu(hidden @ w2 + b2)
    return softmax(hidden_2 @ w3 + b3).argmax(axis=1)


def create_fine_tuning_job(train_path: Path, valid_path: Path, base_model: str, suffix: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is required to create a fine-tuning job.")

    client = OpenAI(api_key=api_key)
    with train_path.open("rb") as train_file:
        train_upload = client.files.create(file=train_file, purpose="fine-tune")

    valid_upload = None
    if valid_path.exists() and valid_path.stat().st_size > 0:
        with valid_path.open("rb") as valid_file:
            valid_upload = client.files.create(file=valid_file, purpose="fine-tune")

    job = client.fine_tuning.jobs.create(
        model=base_model,
        training_file=train_upload.id,
        validation_file=valid_upload.id if valid_upload else None,
        suffix=suffix,
    )
    return {
        "job_id": job.id,
        "base_model": base_model,
        "training_file_id": train_upload.id,
        "validation_file_id": valid_upload.id if valid_upload else None,
        "status": getattr(job, "status", "created"),
    }


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset).resolve()
    print(f"Loading dataset from: {dataset_path}")

    raw_df = load_dataset(dataset_path, args.text_column, args.label_column)
    df = enrich_dataset(raw_df)
    train_df, valid_df = maybe_split_dataset(df, args.test_size, args.random_state)
    local_model = train_mlp(
        train_df=train_df,
        valid_df=valid_df,
        max_features=args.max_features,
        hidden_size=args.hidden_size,
        hidden_size_2=args.hidden_size_2,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        random_state=args.random_state,
    )

    train_rows = [build_fine_tune_record(row.text, row.intent) for row in train_df.itertuples(index=False)]
    valid_rows = [build_fine_tune_record(row.text, row.intent) for row in valid_df.itertuples(index=False)]
    write_jsonl(TRAIN_JSONL_PATH, train_rows)
    write_jsonl(VALID_JSONL_PATH, valid_rows)

    metadata = {
        "provider": "local_numpy",
        "training_type": "supervised_neural_intent_classification",
        "dataset_path": str(dataset_path),
        "row_count": int(len(df)),
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(valid_df)),
        "intents": sorted(df["intent"].unique().tolist()),
        "local_model": local_model,
        "base_model": args.base_model,
        "train_jsonl": str(TRAIN_JSONL_PATH),
        "validation_jsonl": str(VALID_JSONL_PATH),
        "job": None,
    }

    if args.create_job:
        job_info = create_fine_tuning_job(TRAIN_JSONL_PATH, VALID_JSONL_PATH, args.base_model, args.suffix)
        metadata["job"] = job_info
        print(f"Created fine-tuning job: {job_info['job_id']}")

    with METADATA_PATH.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, ensure_ascii=False, indent=2)

    print(f"Prepared {len(train_rows)} training examples at: {TRAIN_JSONL_PATH}")
    if valid_rows:
        print(f"Prepared {len(valid_rows)} validation examples at: {VALID_JSONL_PATH}")
    print(f"Trained local neural intent model at: {LOCAL_MODEL_PATH}")
    print(f"Saved metadata to: {METADATA_PATH}")


if __name__ == "__main__":
    main()
