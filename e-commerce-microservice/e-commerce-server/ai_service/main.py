import json
import os
import re
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

from retrieval import RetrievalDoc, detect_scope, is_neo4j_configured, search_retrieval_docs

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - handled at runtime through healthcheck/fallbacks
    genai = None
    genai_types = None

app = FastAPI(title="AI Service for E-commerce")
router = APIRouter(prefix="/api/ai")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
TRAINING_METADATA_PATH = os.path.join(MODELS_DIR, "training_metadata.json")
INTENT_MODEL_PATH = os.path.join(MODELS_DIR, "intent_mlp_model.npz")
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").strip().lower()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_MAX_OUTPUT_TOKENS = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "700"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", str(OPENAI_MAX_OUTPUT_TOKENS)))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


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


INTENT_RESPONSES = {
    "greeting": "Xin chào! Mình có thể hỗ trợ tìm sản phẩm, đơn hàng, hoặc thông tin khách hàng.",
    "product_inquiry": "Mình đang kiểm tra dữ liệu sản phẩm liên quan cho bạn.",
    "order_status": "Mình đang kiểm tra trạng thái đơn hàng liên quan cho bạn.",
    "complaint": "Mình rất tiếc về trải nghiệm này. Hãy cho mình thêm chi tiết để hỗ trợ tốt hơn.",
    "farewell": "Tạm biệt! Nếu cần tra cứu thêm, cứ nhắn mình nhé.",
    "customer_lookup": "Mình đang kiểm tra hồ sơ khách hàng liên quan cho bạn.",
    "unknown": "Mình chưa hiểu rõ yêu cầu. Bạn có thể diễn đạt cụ thể hơn không?",
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

INTENT_TO_RAG_SCOPE = {
    "product_inquiry": "products",
    "order_status": "orders",
    "customer_lookup": "users",
}

openai_client: Optional[OpenAI] = None
gemini_client = None
training_metadata = {}
intent_model = None


@app.on_event("startup")
def load_runtime_state():
    global openai_client, gemini_client, training_metadata, intent_model

    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print(f"OpenAI client configured with model '{OPENAI_MODEL}'.", flush=True)

    if GEMINI_API_KEY and genai:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"Gemini client configured with model '{GEMINI_MODEL}'.", flush=True)
    elif GEMINI_API_KEY and not genai:
        print("WARNING: GEMINI_API_KEY is set but google-genai is not installed.", flush=True)

    if not _is_llm_configured():
        print("WARNING: No configured LLM provider. /chat will use local fallback responses.", flush=True)

    if os.path.exists(TRAINING_METADATA_PATH):
        with open(TRAINING_METADATA_PATH, "r", encoding="utf-8") as file:
            training_metadata = json.load(file)

    intent_model = _load_intent_model()
    if intent_model:
        print(f"Local neural intent model loaded from '{INTENT_MODEL_PATH}'.", flush=True)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _tokenize_for_intent_model(text: str) -> List[str]:
    normalized = _normalize_text(text)
    words = re.findall(r"[\wÀ-ỹ]+", normalized, flags=re.UNICODE)
    features: List[str] = []

    for word in words:
        features.append(f"w:{word}")

    for first, second in zip(words, words[1:]):
        features.append(f"b:{first}_{second}")

    compact = normalized.replace(" ", "_")
    for size in (3, 4):
        if len(compact) >= size:
            features.extend(f"c:{compact[index:index + size]}" for index in range(len(compact) - size + 1))

    return features


def _load_intent_model():
    if not os.path.exists(INTENT_MODEL_PATH):
        return None

    try:
        payload = np.load(INTENT_MODEL_PATH, allow_pickle=False)
        return {
            "w1": payload["w1"],
            "b1": payload["b1"],
            "w2": payload["w2"],
            "b2": payload["b2"],
            "w3": payload["w3"],
            "b3": payload["b3"],
            "vocab": json.loads(str(payload["vocab"].item())),
            "labels": json.loads(str(payload["labels"].item())),
        }
    except Exception as exc:
        print(f"WARNING: Failed to load local intent model: {exc}", flush=True)
        return None


def _vectorize_intent_text(text: str, vocab: dict) -> np.ndarray:
    features = np.zeros((1, len(vocab)), dtype=np.float32)
    tokens = _tokenize_for_intent_model(text)
    if not tokens:
        return features

    for token in tokens:
        column_index = vocab.get(token)
        if column_index is not None:
            features[0, column_index] = 1.0
    return features


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp_values = np.exp(shifted)
    return exp_values / exp_values.sum(axis=1, keepdims=True)


def _predict_neural_intent(message: str) -> tuple[Optional[str], float]:
    if not intent_model:
        return None, 0.0

    features = _vectorize_intent_text(message, intent_model["vocab"])
    if features.sum() <= 0:
        return None, 0.0

    hidden = np.maximum(features @ intent_model["w1"] + intent_model["b1"], 0.0)
    hidden_2 = np.maximum(hidden @ intent_model["w2"] + intent_model["b2"], 0.0)
    probabilities = _softmax(hidden_2 @ intent_model["w3"] + intent_model["b3"])[0]
    best_index = int(probabilities.argmax())
    return str(intent_model["labels"][best_index]), float(probabilities[best_index])


def _detect_rule_based_intent(message: str) -> Optional[str]:
    lowered = _normalize_text(message)
    for intent, keywords in GENERAL_INTENT_HINTS.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    for intent, keywords in DOMAIN_INTENT_HINTS.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    return None


def _resolve_intent(message: str) -> tuple[Optional[str], float, str]:
    neural_intent, neural_confidence = _predict_neural_intent(message)
    rule_based_intent = _detect_rule_based_intent(message)

    if neural_intent and neural_confidence >= 0.35:
        return neural_intent, neural_confidence, "local_neural_mlp"

    if rule_based_intent:
        return rule_based_intent, 0.25, "rule_based"

    if neural_intent:
        return neural_intent, neural_confidence, "local_neural_mlp_low_confidence"

    return None, 0.0, "none"


def _is_rag_query(message: str) -> bool:
    lowered = _normalize_text(message)
    return any(keyword in lowered for keywords in DOMAIN_INTENT_HINTS.values() for keyword in keywords) or bool(
        re.search(r"\b\d+\b", lowered)
    )


def _scope_for_intent(intent: Optional[str], message: str) -> Optional[str]:
    return INTENT_TO_RAG_SCOPE.get(intent or "") or detect_scope(message)


def _format_product_response(doc: RetrievalDoc) -> str:
    product = doc.payload
    current_price = product.get("current_price")
    discount_price = product.get("discount_price")
    price_line = (
        f"{current_price:,.0f} {product.get('currency', 'VND')}"
        if isinstance(current_price, (int, float))
        else str(current_price)
    )
    if discount_price and discount_price != current_price:
        price_line = (
            f"{price_line} (giảm từ {float(product.get('price', 0)):,.0f} {product.get('currency', 'VND')})"
        )
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


def _summarize_retrieval_doc(doc: RetrievalDoc) -> str:
    if doc.entity_type == "product":
        body = _format_product_response(doc)
    elif doc.entity_type == "order":
        body = _format_order_response(doc)
    else:
        body = _format_customer_response(doc)
    return f"[{doc.entity_type}:{doc.entity_id}] {doc.title}\n{body}"


def _build_sources(docs: List[RetrievalDoc]) -> List[dict]:
    return [
        {
            "entity_type": doc.entity_type,
            "entity_id": doc.entity_id,
            "title": doc.title,
            "score": round(doc.score, 4),
        }
        for doc in docs
    ]


def _extract_json_object(raw_text: str) -> dict:
    cleaned = (raw_text or "").strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _extract_output_text(response) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    collected: List[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text_value = getattr(content, "text", None)
            if text_value:
                collected.append(text_value)
    return "\n".join(collected).strip()


def _is_llm_configured() -> bool:
    if AI_PROVIDER == "gemini":
        return bool(gemini_client)
    if AI_PROVIDER == "openai":
        return bool(openai_client)
    return bool(openai_client or gemini_client)


def _active_provider() -> str:
    if AI_PROVIDER == "gemini" and gemini_client:
        return "gemini"
    if AI_PROVIDER == "openai" and openai_client:
        return "openai"
    if gemini_client:
        return "gemini"
    if openai_client:
        return "openai"
    return "local"


def _build_chat_prompts(message: str, docs: List[RetrievalDoc], suggested_intent: Optional[str]) -> tuple[str, str]:
    rag_scope = detect_scope(message)
    context_blocks = [_summarize_retrieval_doc(doc) for doc in docs]
    context_text = "\n\n".join(context_blocks) if context_blocks else "Không có tài liệu truy xuất phù hợp."
    developer_prompt = (
        "Bạn là trợ lý AI cho hệ thống e-commerce nội bộ.\n"
        "Nhiệm vụ của bạn là trả lời bằng tiếng Việt, ngắn gọn, chính xác và hữu ích.\n"
        "Nếu có context RAG, chỉ dựa trên context đó cho các dữ liệu cụ thể như đơn hàng, sản phẩm, khách hàng.\n"
        "Nếu context không đủ, hãy nói rõ giới hạn và đề nghị người dùng cung cấp thêm mã đơn hàng, SKU, email hoặc tên.\n"
        "Bạn phải trả về JSON hợp lệ với các khóa: intent, confidence, answer.\n"
        "intent phải là một trong: greeting, product_inquiry, order_status, complaint, farewell, customer_lookup, knowledge_lookup, unknown.\n"
        "confidence là số từ 0 đến 1.\n"
        "answer là câu trả lời cuối cùng cho người dùng.\n"
        "Không bịa ra dữ liệu không có trong context."
    )
    user_prompt = (
        f"Suggested intent: {suggested_intent or 'unknown'}\n"
        f"Detected scope: {rag_scope or 'none'}\n"
        f"User message: {message}\n\n"
        f"RAG context:\n{context_text}"
    )
    return developer_prompt, user_prompt


def _chat_response_from_payload(payload: dict, docs: List[RetrievalDoc], suggested_intent: Optional[str]) -> ChatResponse:
    intent = str(payload.get("intent") or suggested_intent or "unknown")
    answer = str(payload.get("answer") or INTENT_RESPONSES["unknown"]).strip()
    confidence = payload.get("confidence", 0.0)
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = 0.0
    confidence_value = max(0.0, min(1.0, confidence_value))

    return ChatResponse(
        intent=intent,
        response=answer,
        confidence=confidence_value,
        sources=_build_sources(docs),
    )


def _fallback_chat(docs: List[RetrievalDoc], suggested_intent: Optional[str]) -> ChatResponse:
    fallback_intent = suggested_intent or "unknown"
    return ChatResponse(
        intent=fallback_intent,
        response=INTENT_RESPONSES.get(fallback_intent, INTENT_RESPONSES["unknown"]),
        confidence=0.2,
        sources=_build_sources(docs),
    )


def _openai_chat(message: str, docs: List[RetrievalDoc], suggested_intent: Optional[str]) -> ChatResponse:
    if not openai_client:
        fallback_intent = suggested_intent or "unknown"
        return ChatResponse(
            intent=fallback_intent,
            response=INTENT_RESPONSES.get(fallback_intent, INTENT_RESPONSES["unknown"]),
            confidence=0.2,
            sources=_build_sources(docs),
        )

    developer_prompt, user_prompt = _build_chat_prompts(message, docs, suggested_intent)
    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS,
        input=[
            {"role": "developer", "content": [{"type": "input_text", "text": developer_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
    )

    return _chat_response_from_payload(_extract_json_object(_extract_output_text(response)), docs, suggested_intent)


def _gemini_chat(message: str, docs: List[RetrievalDoc], suggested_intent: Optional[str]) -> ChatResponse:
    if not gemini_client:
        return _fallback_chat(docs, suggested_intent)

    developer_prompt, user_prompt = _build_chat_prompts(message, docs, suggested_intent)
    config = genai_types.GenerateContentConfig(
        system_instruction=developer_prompt,
        max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
        response_mime_type="application/json",
    )
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=config,
    )
    return _chat_response_from_payload(_extract_json_object(response.text), docs, suggested_intent)


def _llm_chat(message: str, docs: List[RetrievalDoc], suggested_intent: Optional[str]) -> ChatResponse:
    provider = _active_provider()
    if provider == "gemini":
        return _gemini_chat(message, docs, suggested_intent)
    if provider == "openai":
        return _openai_chat(message, docs, suggested_intent)
    return _fallback_chat(docs, suggested_intent)


@router.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "service": "ai_service",
        "ai_provider": AI_PROVIDER,
        "active_provider": _active_provider(),
        "openai_configured": bool(openai_client),
        "openai_model": OPENAI_MODEL,
        "gemini_configured": bool(gemini_client),
        "gemini_model": GEMINI_MODEL,
        "neo4j_configured": is_neo4j_configured(),
        "local_intent_model_configured": bool(intent_model),
        "local_intent_model_path": INTENT_MODEL_PATH if intent_model else None,
        "training_metadata": training_metadata or None,
    }


@router.post("/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    message = (request.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message must not be empty")

    resolved_intent, intent_confidence, intent_source = _resolve_intent(message)
    rag_scope = _scope_for_intent(resolved_intent, message)
    should_use_rag = resolved_intent in ("product_inquiry", "order_status", "customer_lookup") or _is_rag_query(message)
    docs = search_retrieval_docs(message, top_k=3, scope=rag_scope) if should_use_rag else []

    try:
        response = _llm_chat(message, docs, resolved_intent or ("knowledge_lookup" if docs else None))
        if not docs and response.confidence <= 0.2 and resolved_intent:
            response.intent = resolved_intent
            response.confidence = round(intent_confidence, 4)
            response.response = INTENT_RESPONSES.get(resolved_intent, response.response)
        response.sources.append(
            {
                "entity_type": "intent_classifier",
                "entity_id": intent_source,
                "title": resolved_intent or "unknown",
                "score": round(intent_confidence, 4),
            }
        )
        return response
    except Exception as exc:
        fallback_intent = resolved_intent or ("knowledge_lookup" if docs else "unknown")
        fallback_response = INTENT_RESPONSES.get(fallback_intent, INTENT_RESPONSES["unknown"])
        raise HTTPException(
            status_code=502,
            detail={
                "message": "AI provider request failed",
                "provider": _active_provider(),
                "error": str(exc),
                "fallback_intent": fallback_intent,
                "fallback_response": fallback_response,
            },
        ) from exc


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
    if len(request.historical_sales) < 1:
        raise HTTPException(status_code=400, detail="Not enough historical data")

    recent_months = request.historical_sales[-3:]
    avg_recent = sum(recent_months) / len(recent_months)
    overall_avg = sum(request.historical_sales) / len(request.historical_sales)

    prediction = avg_recent * 1.05

    if prediction > overall_avg:
        trend = "UPWARD"
    elif prediction < overall_avg:
        trend = "DOWNWARD"
    else:
        trend = "STABLE"

    return TrendResponse(predicted_sales=round(prediction, 2), trend=trend)


app.include_router(router)
