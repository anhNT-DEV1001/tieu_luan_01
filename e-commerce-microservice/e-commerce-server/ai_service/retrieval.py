import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SERVICE_URLS = {
    "users": os.getenv("USER_SERVICE_URL", "http://ecommerce-user-service:8001/api/users/"),
    "products": os.getenv("PRODUCT_SERVICE_URL", "http://ecommerce-product-service:8002/api/products/"),
    "orders": os.getenv("ORDER_SERVICE_URL", "http://ecommerce-order-service:8003/api/orders/"),
}

REQUEST_TIMEOUT = float(os.getenv("AI_SERVICE_TIMEOUT", "8"))

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
                builder = {
                    "products": _build_product_doc,
                    "orders": _build_order_doc,
                    "users": _build_user_doc,
                }[service_name]
                docs.append(builder(detail))
                continue

        try:
            collection = _fetch_collection(service_name)
        except requests.RequestException:
            continue

        builder = {
            "products": _build_product_doc,
            "orders": _build_order_doc,
            "users": _build_user_doc,
        }[service_name]
        docs.extend(builder(item) for item in collection)

    return docs


def search_retrieval_docs(query: str, top_k: int = 3, scope: Optional[str] = None) -> List[RetrievalDoc]:
    if not (query or "").strip():
        return []
    ranked_docs = _rank_docs(query, build_retrieval_docs(query=query, scope=scope))
    return ranked_docs[: max(1, top_k)]
