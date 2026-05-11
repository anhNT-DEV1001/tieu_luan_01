import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from neo4j import GraphDatabase
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - optional provider dependency
    genai = None
    genai_types = None

SERVICE_URLS = {
    "users": os.getenv("USER_SERVICE_URL", "http://ecommerce-user-service:8001/api/users/"),
    "products": os.getenv("PRODUCT_SERVICE_URL", "http://ecommerce-product-service:8002/api/products/"),
    "orders": os.getenv("ORDER_SERVICE_URL", "http://ecommerce-order-service:8003/api/orders/"),
}


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default

REQUEST_TIMEOUT = float(os.getenv("AI_SERVICE_TIMEOUT", "8"))
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
NEO4J_VECTOR_INDEX = os.getenv("NEO4J_VECTOR_INDEX", "document_embeddings")
AI_PROVIDER = _env("AI_PROVIDER", "openai").strip().lower()
AI_EMBEDDING_PROVIDER = _env("AI_EMBEDDING_PROVIDER", AI_PROVIDER).strip().lower()
OPENAI_EMBEDDING_MODEL = _env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
GEMINI_EMBEDDING_MODEL = _env("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_MODEL = _env(
    "AI_EMBEDDING_MODEL",
    GEMINI_EMBEDDING_MODEL if AI_EMBEDDING_PROVIDER == "gemini" else OPENAI_EMBEDDING_MODEL,
)
EMBEDDING_DIMENSIONS = int(
    _env(
        "AI_EMBEDDING_DIMENSIONS",
        _env("GEMINI_EMBEDDING_DIMENSIONS" if AI_EMBEDDING_PROVIDER == "gemini" else "OPENAI_EMBEDDING_DIMENSIONS", "1536"),
    )
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

DOMAIN_KEYWORDS = {
    "orders": (
        "order",
        "orders",
        "đơn hàng",
        "don hang",
        "mua",
        "shipping",
        "ship",
        "track",
        "status",
        "trạng thái",
    ),
    "products": (
        "product",
        "products",
        "sản phẩm",
        "san pham",
        "item",
        "price",
        "giá",
        "stock",
        "inventory",
        "category",
        "danh mục",
    ),
    "users": (
        "customer",
        "customers",
        "khách hàng",
        "khach hang",
        "user",
        "users",
        "profile",
        "email",
        "phone",
        "loyalty",
    ),
}

SCOPE_TO_ENTITY_TYPE = {
    "products": "product",
    "orders": "order",
    "users": "customer",
}

SERVICE_TO_ENTITY_TYPE = {
    "products": "product",
    "orders": "order",
    "users": "customer",
}

_neo4j_driver = None
_openai_embedding_client = None
_gemini_embedding_client = None


@dataclass
class RetrievalDoc:
    entity_type: str
    entity_id: str
    title: str
    text: str
    payload: Dict[str, Any]
    score: float = 0.0


def _safe_get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _extract_results(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, list):
            return results
        return [payload]
    if isinstance(payload, list):
        return payload
    return []


def _collection_url(service_name: str) -> str:
    return SERVICE_URLS[service_name]


def _detail_url(service_name: str, entity_id: Any) -> str:
    base_url = SERVICE_URLS[service_name]
    return f"{base_url.rstrip('/')}/{entity_id}/"


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)


def _build_product_doc(product: Dict[str, Any]) -> RetrievalDoc:
    searchable_text = " | ".join(
        [
            _normalize(product.get("name")),
            _normalize(product.get("sku")),
            _normalize(product.get("category")),
            _normalize(product.get("brand")),
            _normalize(product.get("description")),
            " ".join(product.get("tags") or []),
            _normalize(product.get("color")),
            _normalize(product.get("material")),
            _normalize(product.get("size")),
            _normalize(product.get("origin_country")),
            _normalize(product.get("attributes")),
        ]
    )
    title = f"{product.get('name', 'Product')} ({product.get('sku', '')})"
    return RetrievalDoc("product", str(product.get("id", "")), title, searchable_text, product)


def _build_order_doc(order: Dict[str, Any]) -> RetrievalDoc:
    item_lines = []
    for item in order.get("items") or []:
        item_lines.append(
            " ".join(
                [
                    _normalize(item.get("product_name")),
                    _normalize(item.get("sku")),
                    f"x{item.get('quantity', 0)}",
                    _normalize(item.get("line_total")),
                ]
            )
        )
    searchable_text = " | ".join(
        [
            _normalize(order.get("id")),
            _normalize(order.get("customer_name")),
            _normalize(order.get("customer_email")),
            _normalize(order.get("shipping_address")),
            _normalize(order.get("shipping_city")),
            _normalize(order.get("status")),
            _normalize(order.get("total_amount")),
            _normalize(order.get("notes")),
            " ".join(item_lines),
        ]
    )
    title = f"Order #{order.get('id', '')} - {order.get('customer_name', 'Customer')}"
    return RetrievalDoc("order", str(order.get("id", "")), title, searchable_text, order)


def _build_user_doc(user: Dict[str, Any]) -> RetrievalDoc:
    searchable_text = " | ".join(
        [
            _normalize(user.get("full_name")),
            _normalize(user.get("email")),
            _normalize(user.get("phone")),
            _normalize(user.get("role")),
            _normalize(user.get("status")),
            _normalize(user.get("city")),
            _normalize(user.get("country")),
            _normalize(user.get("address")),
            _normalize(user.get("loyalty_points")),
            _normalize(user.get("metadata")),
        ]
    )
    title = f"{user.get('full_name', 'Customer')} ({user.get('email', '')})"
    return RetrievalDoc("customer", str(user.get("id", "")), title, searchable_text, user)


ENTITY_BUILDERS = {
    "products": _build_product_doc,
    "orders": _build_order_doc,
    "users": _build_user_doc,
}


def detect_scope(query: str) -> Optional[str]:
    lowered = (query or "").lower()
    for scope, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return scope
    return None


def _fetch_collection(service_name: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    payload = _safe_get_json(_collection_url(service_name), params=params)
    return _extract_results(payload)


def _fetch_detail(service_name: str, entity_id: Any) -> Optional[Dict[str, Any]]:
    try:
        payload = _safe_get_json(_detail_url(service_name, entity_id))
    except requests.RequestException:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def _maybe_entity_id(query: str) -> Optional[str]:
    match = re.search(r"(?:order|product|customer|user|khach hang|khách hàng)\s*#?\s*(\d+)", query, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    if re.fullmatch(r"\s*\d+\s*", query or ""):
        return (query or "").strip()
    return None


def _rank_docs(query: str, docs: List[RetrievalDoc]) -> List[RetrievalDoc]:
    if not docs:
        return []

    corpus = [doc.text for doc in docs]
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True)
    matrix = vectorizer.fit_transform(corpus + [query or ""])
    query_vector = matrix[-1]
    doc_matrix = matrix[:-1]
    scores = cosine_similarity(query_vector, doc_matrix).flatten()

    ranked_docs = []
    for doc, score in zip(docs, scores):
        ranked_docs.append(
            RetrievalDoc(
                entity_type=doc.entity_type,
                entity_id=doc.entity_id,
                title=doc.title,
                text=doc.text,
                payload=doc.payload,
                score=float(score),
            )
        )

    ranked_docs.sort(key=lambda item: item.score, reverse=True)
    return ranked_docs


def get_openai_embedding_client() -> Optional[OpenAI]:
    global _openai_embedding_client
    if not OPENAI_API_KEY:
        return None
    if _openai_embedding_client is None:
        _openai_embedding_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_embedding_client


def get_gemini_embedding_client():
    global _gemini_embedding_client
    if not GEMINI_API_KEY or not genai:
        return None
    if _gemini_embedding_client is None:
        _gemini_embedding_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_embedding_client


def _openai_embed_text(text: str) -> Optional[List[float]]:
    client = get_openai_embedding_client()
    if not client:
        return None
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text, dimensions=EMBEDDING_DIMENSIONS)
    return response.data[0].embedding


def _gemini_embed_text(text: str) -> Optional[List[float]]:
    client = get_gemini_embedding_client()
    if not client:
        return None
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=genai_types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    if not response.embeddings:
        return None
    return list(response.embeddings[0].values)


def embed_text(text: str) -> Optional[List[float]]:
    if not (text or "").strip():
        return None
    if AI_EMBEDDING_PROVIDER == "gemini":
        return _gemini_embed_text(text)
    if AI_EMBEDDING_PROVIDER == "openai":
        return _openai_embed_text(text)
    return _gemini_embed_text(text) or _openai_embed_text(text)


def get_neo4j_driver():
    global _neo4j_driver
    if not NEO4J_URI:
        return None
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    return _neo4j_driver


def is_neo4j_configured() -> bool:
    return bool(NEO4J_URI)


def build_retrieval_docs(query: str, scope: Optional[str] = None) -> List[RetrievalDoc]:
    resolved_scope = scope or detect_scope(query)
    service_names = [resolved_scope] if resolved_scope else ["products", "orders", "users"]
    docs: List[RetrievalDoc] = []

    entity_id = _maybe_entity_id(query)
    for service_name in service_names:
        if service_name is None:
            continue
        if entity_id:
            detail = _fetch_detail(service_name, entity_id)
            if detail:
                docs.append(ENTITY_BUILDERS[service_name](detail))
                continue

        try:
            collection = _fetch_collection(service_name)
        except requests.RequestException:
            continue

        docs.extend(ENTITY_BUILDERS[service_name](item) for item in collection)

    return docs


def _query_neo4j_exact_entity(query: str, scope: Optional[str], top_k: int) -> List[RetrievalDoc]:
    driver = get_neo4j_driver()
    entity_id = _maybe_entity_id(query)
    if not driver or not entity_id:
        return []

    entity_type = SCOPE_TO_ENTITY_TYPE.get(scope or "", None)
    cypher = """
    MATCH (d:Document)
    WHERE d.entity_id = $entity_id
      AND ($entity_type IS NULL OR d.entity_type = $entity_type)
    RETURN d
    LIMIT $top_k
    """
    records, _, _ = driver.execute_query(
        cypher,
        entity_id=entity_id,
        entity_type=entity_type,
        top_k=max(1, top_k),
        database_=NEO4J_DATABASE,
    )
    return [_record_to_doc(record["d"], fallback_score=1.0) for record in records]


def _query_neo4j_vector(query: str, scope: Optional[str], top_k: int) -> List[RetrievalDoc]:
    driver = get_neo4j_driver()
    query_embedding = embed_text(query)
    if not driver or not query_embedding:
        return []

    entity_type = SCOPE_TO_ENTITY_TYPE.get(scope or "", None)
    cypher = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
    YIELD node, score
    WHERE $entity_type IS NULL OR node.entity_type = $entity_type
    RETURN node AS d, score
    ORDER BY score DESC
    LIMIT $top_k
    """
    records, _, _ = driver.execute_query(
        cypher,
        index_name=NEO4J_VECTOR_INDEX,
        top_k=max(1, top_k),
        embedding=query_embedding,
        entity_type=entity_type,
        database_=NEO4J_DATABASE,
    )
    return [_record_to_doc(record["d"], fallback_score=float(record["score"])) for record in records]


def _record_to_doc(node, fallback_score: float = 0.0) -> RetrievalDoc:
    payload_json = node.get("payload_json")
    try:
        payload = json.loads(payload_json) if payload_json else {}
    except json.JSONDecodeError:
        payload = {}
    return RetrievalDoc(
        entity_type=node.get("entity_type", "unknown"),
        entity_id=str(node.get("entity_id", "")),
        title=node.get("title", "Untitled"),
        text=node.get("text", ""),
        payload=payload,
        score=float(node.get("score", fallback_score)),
    )


def _search_neo4j_docs(query: str, top_k: int = 3, scope: Optional[str] = None) -> List[RetrievalDoc]:
    try:
        exact_docs = _query_neo4j_exact_entity(query, scope=scope, top_k=top_k)
        if exact_docs:
            return exact_docs[: max(1, top_k)]

        vector_docs = _query_neo4j_vector(query, scope=scope, top_k=top_k)
        if vector_docs:
            return vector_docs[: max(1, top_k)]
    except Exception:
        return []
    return []


def search_retrieval_docs(query: str, top_k: int = 3, scope: Optional[str] = None) -> List[RetrievalDoc]:
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []

    if is_neo4j_configured():
        neo4j_docs = _search_neo4j_docs(normalized_query, top_k=top_k, scope=scope)
        if neo4j_docs:
            return neo4j_docs

    ranked_docs = _rank_docs(normalized_query, build_retrieval_docs(query=normalized_query, scope=scope))
    return ranked_docs[: max(1, top_k)]
