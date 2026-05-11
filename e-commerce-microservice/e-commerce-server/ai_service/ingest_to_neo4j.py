import json
from typing import Dict, List

from retrieval import (
    ENTITY_BUILDERS,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    NEO4J_DATABASE,
    NEO4J_VECTOR_INDEX,
    SERVICE_TO_ENTITY_TYPE,
    SERVICE_URLS,
    embed_text,
    _fetch_collection,
    get_neo4j_driver,
)


def _safe_json(value):
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return json.dumps({}, ensure_ascii=False)


def _ensure_indexes(driver) -> None:
    driver.execute_query(
        """
        CREATE CONSTRAINT document_doc_id IF NOT EXISTS
        FOR (d:Document) REQUIRE d.doc_id IS UNIQUE
        """,
        database_=NEO4J_DATABASE,
    )
    driver.execute_query(
        """
        CREATE CONSTRAINT product_id IF NOT EXISTS
        FOR (p:Product) REQUIRE p.id IS UNIQUE
        """,
        database_=NEO4J_DATABASE,
    )
    driver.execute_query(
        """
        CREATE CONSTRAINT customer_id IF NOT EXISTS
        FOR (c:Customer) REQUIRE c.id IS UNIQUE
        """,
        database_=NEO4J_DATABASE,
    )
    driver.execute_query(
        """
        CREATE CONSTRAINT order_id IF NOT EXISTS
        FOR (o:Order) REQUIRE o.id IS UNIQUE
        """,
        database_=NEO4J_DATABASE,
    )
    driver.execute_query(
        """
        CREATE CONSTRAINT category_name IF NOT EXISTS
        FOR (c:Category) REQUIRE c.name IS UNIQUE
        """,
        database_=NEO4J_DATABASE,
    )
    driver.execute_query(
        """
        CREATE CONSTRAINT brand_name IF NOT EXISTS
        FOR (b:Brand) REQUIRE b.name IS UNIQUE
        """,
        database_=NEO4J_DATABASE,
    )
    driver.execute_query(
        f"""
        CREATE VECTOR INDEX {NEO4J_VECTOR_INDEX} IF NOT EXISTS
        FOR (d:Document) ON d.embedding
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {EMBEDDING_DIMENSIONS},
            `vector.similarity_function`: 'cosine'
        }}}}
        """,
        database_=NEO4J_DATABASE,
    )
    driver.execute_query(
        """
        CALL db.awaitIndexes()
        """,
        database_=NEO4J_DATABASE,
    )


def _upsert_product(driver, payload: Dict) -> None:
    driver.execute_query(
        """
        MERGE (p:Product {id: $id})
        SET p.name = $name,
            p.sku = $sku,
            p.category = $category,
            p.brand = $brand,
            p.price = $price,
            p.discount_price = $discount_price,
            p.stock_quantity = $stock_quantity,
            p.rating = $rating,
            p.payload_json = $payload_json
        WITH p
        MERGE (c:Category {name: coalesce($category, 'Unknown')})
        MERGE (b:Brand {name: coalesce($brand, 'Unknown')})
        MERGE (p)-[:BELONGS_TO]->(c)
        MERGE (p)-[:MADE_BY]->(b)
        """,
        id=str(payload.get("id", "")),
        name=payload.get("name"),
        sku=payload.get("sku"),
        category=payload.get("category"),
        brand=payload.get("brand"),
        price=payload.get("price"),
        discount_price=payload.get("discount_price"),
        stock_quantity=payload.get("stock_quantity"),
        rating=payload.get("rating"),
        payload_json=_safe_json(payload),
        database_=NEO4J_DATABASE,
    )


def _upsert_customer(driver, payload: Dict) -> None:
    driver.execute_query(
        """
        MERGE (c:Customer {id: $id})
        SET c.full_name = $full_name,
            c.email = $email,
            c.phone = $phone,
            c.role = $role,
            c.status = $status,
            c.city = $city,
            c.country = $country,
            c.loyalty_points = $loyalty_points,
            c.payload_json = $payload_json
        """,
        id=str(payload.get("id", "")),
        full_name=payload.get("full_name"),
        email=payload.get("email"),
        phone=payload.get("phone"),
        role=payload.get("role"),
        status=payload.get("status"),
        city=payload.get("city"),
        country=payload.get("country"),
        loyalty_points=payload.get("loyalty_points"),
        payload_json=_safe_json(payload),
        database_=NEO4J_DATABASE,
    )


def _upsert_order(driver, payload: Dict) -> None:
    driver.execute_query(
        """
        MERGE (o:Order {id: $id})
        SET o.customer_name = $customer_name,
            o.customer_email = $customer_email,
            o.status = $status,
            o.total_amount = $total_amount,
            o.shipping_city = $shipping_city,
            o.shipping_address = $shipping_address,
            o.payload_json = $payload_json
        WITH o
        MERGE (c:Customer {id: $user_id})
        ON CREATE SET c.full_name = $customer_name, c.email = $customer_email
        MERGE (c)-[:PLACED]->(o)
        """,
        id=str(payload.get("id", "")),
        user_id=str(payload.get("user_id", "")),
        customer_name=payload.get("customer_name"),
        customer_email=payload.get("customer_email"),
        status=payload.get("status"),
        total_amount=payload.get("total_amount"),
        shipping_city=payload.get("shipping_city"),
        shipping_address=payload.get("shipping_address"),
        payload_json=_safe_json(payload),
        database_=NEO4J_DATABASE,
    )
    for item in payload.get("items") or []:
        driver.execute_query(
            """
            MERGE (o:Order {id: $order_id})
            MERGE (p:Product {id: $product_id})
            ON CREATE SET p.name = $product_name, p.sku = $sku
            MERGE (o)-[r:CONTAINS]->(p)
            SET r.quantity = $quantity,
                r.line_total = $line_total,
                r.sku = $sku
            """,
            order_id=str(payload.get("id", "")),
            product_id=str(item.get("product_id", "")),
            product_name=item.get("product_name"),
            sku=item.get("sku"),
            quantity=item.get("quantity"),
            line_total=item.get("line_total"),
            database_=NEO4J_DATABASE,
        )


def _upsert_document(driver, entity_type: str, entity_id: str, title: str, text: str, payload: Dict) -> None:
    doc_id = f"{entity_type}:{entity_id}"
    embedding = embed_text(text)
    driver.execute_query(
        """
        MERGE (d:Document {doc_id: $doc_id})
        SET d.entity_type = $entity_type,
            d.entity_id = $entity_id,
            d.scope = $scope,
            d.title = $title,
            d.text = $text,
            d.payload_json = $payload_json,
            d.embedding_model = $embedding_model,
            d.embedding = $embedding
        """,
        doc_id=doc_id,
        entity_type=entity_type,
        entity_id=entity_id,
        scope=f"{entity_type}s",
        title=title,
        text=text,
        payload_json=_safe_json(payload),
        embedding_model=EMBEDDING_MODEL,
        embedding=embedding,
        database_=NEO4J_DATABASE,
    )

    label = {"product": "Product", "customer": "Customer", "order": "Order"}[entity_type]
    driver.execute_query(
        f"""
        MATCH (d:Document {{doc_id: $doc_id}})
        MATCH (e:{label} {{id: $entity_id}})
        MERGE (d)-[:ABOUT]->(e)
        """,
        doc_id=doc_id,
        entity_id=entity_id,
        database_=NEO4J_DATABASE,
    )


def _ingest_service_docs(driver, service_name: str) -> int:
    docs = [ENTITY_BUILDERS[service_name](item) for item in _fetch_collection(service_name)]
    entity_type = SERVICE_TO_ENTITY_TYPE[service_name]
    count = 0
    for doc in docs:
        payload = doc.payload
        if entity_type == "product":
            _upsert_product(driver, payload)
        elif entity_type == "customer":
            _upsert_customer(driver, payload)
        else:
            _upsert_order(driver, payload)
        _upsert_document(driver, doc.entity_type, doc.entity_id, doc.title, doc.text, payload)
        count += 1
    return count


def main() -> None:
    driver = get_neo4j_driver()
    if not driver:
        raise EnvironmentError("NEO4J_URI is required before ingesting data into Neo4j.")

    _ensure_indexes(driver)
    totals: List[str] = []
    for service_name in SERVICE_URLS:
        count = _ingest_service_docs(driver, service_name)
        totals.append(f"{service_name}={count}")

    print("Neo4j ingest completed: " + ", ".join(totals))


if __name__ == "__main__":
    main()
