import json
import os
import pickle
import re
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field
from pydantic import BaseModel

from retrieval import RetrievalDoc, detect_scope, search_retrieval_docs

app = FastAPI(title="AI Service for E-commerce")
router = APIRouter(prefix="/api/ai")

# Allow CORS for local testing if necessary
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
TRAINING_METADATA_PATH = os.path.join(MODELS_DIR, "training_metadata.json")

# Define Data Models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    intent: str
    response: str
    confidence: float
    sources: List[dict] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class SearchHit(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    score: float
    payload: dict


class SearchResponse(BaseModel):
    query: str
    scope: Optional[str] = None
    results: List[SearchHit]

class TrendRequest(BaseModel):
    product_category: str
    historical_sales: List[float]

class TrendResponse(BaseModel):
    predicted_sales: float
    trend: str

# Globals to hold models
chatbot_model = None
vectorizer = None
sentiment_model = None
training_metadata = {}

# Mock Intent Responses
INTENT_RESPONSES = {
    "greeting": "Hello! Welcome to Que Commerce. How can I assist you today?",
    "product_inquiry": "We have a wide range of products! What category are you looking for?",
    "order_status": "Please provide your order ID, and I will check the status for you.",
    "complaint": "I'm sorry to hear that. Could you please provide more details so I can help?",
    "farewell": "Goodbye! Thank you for visiting Que Commerce.",
    "unknown": "I'm not sure I understand. Could you please rephrase?"
}

DOMAIN_INTENT_HINTS = {
    "order_status": ("order", "orders", "đơn hàng", "don hang", "shipment", "tracking", "track", "status", "trạng thái"),
    "product_inquiry": ("product", "products", "sản phẩm", "san pham", "price", "giá", "stock", "inventory", "category"),
    "customer_lookup": ("customer", "customers", "khách hàng", "khach hang", "user", "users", "email", "phone", "loyalty"),
}

GENERAL_INTENT_HINTS = {
    "greeting": ("hi", "hello", "hey", "xin chào", "chao", "chào"),
    "farewell": ("bye", "goodbye", "tạm biệt", "tam biet", "see you"),
    "complaint": ("complaint", "broken", "angry", "issue", "problem", "lỗi", "khó chịu", "khong hai long"),
}

@app.on_event("startup")
def load_models():
    """Load pre-trained models from the models directory."""
    global chatbot_model, vectorizer, sentiment_model, training_metadata
    try:
        with open(os.path.join(MODELS_DIR, "chatbot_intent_model.pkl"), "rb") as f:
            chatbot_model = pickle.load(f)
        with open(os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl"), "rb") as f:
            vectorizer = pickle.load(f)
        if os.path.exists(TRAINING_METADATA_PATH):
            with open(TRAINING_METADATA_PATH, "r", encoding="utf-8") as f:
                training_metadata = json.load(f)
        print("Models loaded successfully.", flush=True)
    except FileNotFoundError:
        print("WARNING: Models not found. Training script needs to be run.", flush=True)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _detect_rule_based_intent(message: str) -> Optional[str]:
    lowered = _normalize_text(message)
    for intent, keywords in GENERAL_INTENT_HINTS.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    for intent, keywords in DOMAIN_INTENT_HINTS.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    return None


def _format_product_response(doc: RetrievalDoc) -> str:
    product = doc.payload
    current_price = product.get("current_price")
    discount_price = product.get("discount_price")
    price_line = f"{current_price:,.0f} {product.get('currency', 'VND')}" if isinstance(current_price, (int, float)) else str(current_price)
    if discount_price and discount_price != current_price:
        price_line = f"{price_line} (giảm từ {float(product.get('price', 0)):,.0f} {product.get('currency', 'VND')})"
    stock_status = "còn hàng" if int(product.get("stock_quantity", 0)) > 0 else "hết hàng"
    return (
        f"Sản phẩm: {product.get('name')} [{product.get('sku')}]\n"
        f"Danh mục: {product.get('category')} | Brand: {product.get('brand')}\n"
        f"Giá hiện tại: {price_line}\n"
        f"Tồn kho: {product.get('stock_quantity')} ({stock_status})\n"
        f"Đánh giá: {product.get('rating')}\n"
        f"Mô tả: {product.get('description') or 'Không có mô tả'}"
    )


def _format_customer_response(doc: RetrievalDoc) -> str:
    customer = doc.payload
    return (
        f"Khách hàng: {customer.get('full_name')} [#{customer.get('id')}]\n"
        f"Email: {customer.get('email')}\n"
        f"Điện thoại: {customer.get('phone') or 'N/A'}\n"
        f"Vai trò: {customer.get('role')} | Trạng thái: {customer.get('status')}\n"
        f"Điểm loyalty: {customer.get('loyalty_points')}\n"
        f"Địa chỉ: {customer.get('address') or 'N/A'}, {customer.get('city') or 'N/A'}, {customer.get('country') or 'N/A'}"
    )


def _format_order_response(doc: RetrievalDoc) -> str:
    order = doc.payload
    items = order.get("items") or []
    item_lines = []
    for item in items[:5]:
        item_lines.append(
            f"- {item.get('product_name')} x{item.get('quantity')} = {float(item.get('line_total', 0)):,.0f}"
        )
    if len(items) > 5:
        item_lines.append(f"- ... và {len(items) - 5} item khác")
    return (
        f"Đơn hàng #{order.get('id')} cho {order.get('customer_name')} ({order.get('customer_email')})\n"
        f"Trạng thái: {order.get('status')}\n"
        f"Tạm tính: {float(order.get('subtotal_amount', 0)):,.0f}\n"
        f"Phí ship: {float(order.get('shipping_fee', 0)):,.0f}\n"
        f"Tổng tiền: {float(order.get('total_amount', 0)):,.0f}\n"
        f"Giao tới: {order.get('shipping_address')}, {order.get('shipping_city')}\n"
        f"Items:\n" + "\n".join(item_lines if item_lines else ["- Không có items"])
    )


def _format_rag_response(query: str, docs: List[RetrievalDoc]) -> tuple[str, List[dict], Optional[str]]:
    if not docs:
        return (
            "Tôi không tìm thấy bản ghi phù hợp trong dữ liệu hiện tại. Hãy thử nêu rõ mã đơn hàng, SKU, email hoặc tên khách hàng.",
            [],
            detect_scope(query),
        )

    top_doc = docs[0]
    if top_doc.entity_type == "product":
        response = _format_product_response(top_doc)
    elif top_doc.entity_type == "order":
        response = _format_order_response(top_doc)
    else:
        response = _format_customer_response(top_doc)

    sources = [
        {
            "entity_type": doc.entity_type,
            "entity_id": doc.entity_id,
            "title": doc.title,
            "score": round(doc.score, 4),
        }
        for doc in docs
    ]
    return response, sources, detect_scope(query)


def _build_fallback_intent(message: str) -> tuple[str, str, float]:
    if not chatbot_model or not vectorizer:
        return "unknown", INTENT_RESPONSES["unknown"], 0.0

    X_input = vectorizer.transform([message.lower()])
    intent_pred = chatbot_model.predict(X_input)[0]
    probabilities = chatbot_model.predict_proba(X_input)[0]
    confidence = max(probabilities)

    if confidence < 0.3:
        intent_pred = "unknown"

    return intent_pred, INTENT_RESPONSES.get(intent_pred, INTENT_RESPONSES["unknown"]), float(confidence)


def _is_rag_query(message: str) -> bool:
    lowered = _normalize_text(message)
    return any(keyword in lowered for keywords in DOMAIN_INTENT_HINTS.values() for keyword in keywords) or bool(
        re.search(r"\b\d+\b", lowered)
    )

@router.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "service": "ai_service",
        "model_ready": bool(chatbot_model and vectorizer),
        "training_metadata": training_metadata or None,
    }

@router.post("/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    rule_based_intent = _detect_rule_based_intent(request.message)
    if rule_based_intent in ("product_inquiry", "order_status", "customer_lookup") or _is_rag_query(request.message):
        docs = search_retrieval_docs(request.message, top_k=3)
        rag_response, sources, scope = _format_rag_response(request.message, docs)
        intent = rule_based_intent or scope or "knowledge_lookup"
        confidence = docs[0].score if docs else 0.0
        return ChatResponse(intent=intent, response=rag_response, confidence=float(confidence), sources=sources)

    intent_pred, bot_reply, confidence = _build_fallback_intent(request.message)
    return ChatResponse(intent=intent_pred, response=bot_reply, confidence=confidence, sources=[])


@router.post("/search", response_model=SearchResponse)
def search_knowledge_base(request: SearchRequest):
    docs = search_retrieval_docs(request.query, top_k=request.top_k)
    results = [
        SearchHit(
            entity_type=doc.entity_type,
            entity_id=doc.entity_id,
            title=doc.title,
            score=doc.score,
            payload=doc.payload,
        )
        for doc in docs
    ]
    return SearchResponse(query=request.query, scope=detect_scope(request.query), results=results)

@router.post("/trends", response_model=TrendResponse)
def predict_trend(request: TrendRequest):
    """
    Very simple trend prediction. 
    In reality, this would load a Scikit-Learn timeseries model.
    Here we implement a mock logic to demonstrate functionality.
    """
    if len(request.historical_sales) < 1:
        raise HTTPException(status_code=400, detail="Not enough historical data")
    
    recent_months = request.historical_sales[-3:]
    avg_recent = sum(recent_months) / len(recent_months)
    overall_avg = sum(request.historical_sales) / len(request.historical_sales)
    
    prediction = avg_recent * 1.05  # predict 5% growth
    
    if prediction > overall_avg:
        trend = "UPWARD"
    elif prediction < overall_avg:
        trend = "DOWNWARD"
    else:
        trend = "STABLE"
        
    return TrendResponse(predicted_sales=round(prediction, 2), trend=trend)

app.include_router(router)
