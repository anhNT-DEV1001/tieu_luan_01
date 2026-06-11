# Phân tích class/thực thể của dự án `e-commerce-microservice`

## 1. Mục tiêu của file note này

File này tổng hợp nhanh các class/thực thể có thể rút ra từ:

- [docs/ecommerce-microservice-report.tex](/home/dezai/Documents/code/TIEU_LUAN/docs/ecommerce-microservice-report.tex)
- [e-commerce-microservice/](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice)

Mục tiêu hiện tại:

- Chưa code ngay.
- Phân tích các thực thể/domain class chính của hệ thống.
- Đề xuất bộ file Java skeleton để import vào Visual Paradigm và dựng class diagram.

## 2. Ranh giới domain / bounded context

Theo báo cáo và source code thực tế, hệ thống đang có các context sau:

1. `User Context` -> `user_service`
2. `Product Context` -> `product_service`
3. `Order Context` -> `order_service`
4. `Payment Context` -> `payment_service`
5. `AI Context` -> `ai_service`
6. `API Composition / Gateway Context` -> `gateway`
7. `Presentation Context` -> `e-commerce-client`

Lưu ý:

- `Cart Context` mới ở mức logic frontend/payload, chưa có microservice riêng.
- `Shipping Context` chưa tách riêng, đang được gộp vào `Order`.

## 3. Danh sách class/thực thể cốt lõi theo source code

### 3.1. User Service

Nguồn chính: [accounts/models.py](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice/e-commerce-server/user_service/accounts/models.py)

#### Entity chính

1. `UserProfile`

Thuộc tính chính:

- `id`
- `full_name`
- `email`
- `phone`
- `role`
- `status`
- `loyalty_points`
- `address`
- `city`
- `country`
- `avatar_url`
- `metadata`
- `created_at`
- `updated_at`

#### Enum nội bộ nên tách ra khi sinh Java

1. `UserRole`
   Giá trị: `ADMIN`, `CUSTOMER`, `STAFF`
2. `UserStatus`
   Giá trị: `ACTIVE`, `INACTIVE`

#### DTO/API class nên có thêm

1. `UserSummary`
2. `UserLoginRequest`
3. `UserLoginResponse`

### 3.2. Product Service

Nguồn chính: [catalog/models.py](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice/e-commerce-server/product_service/catalog/models.py)

#### Entity chính

1. `Product`

Thuộc tính chính:

- `id`
- `sku`
- `name`
- `slug`
- `category`
- `brand`
- `price`
- `discount_price`
- `currency`
- `stock_quantity`
- `safety_stock`
- `rating`
- `weight_grams`
- `dimensions`
- `color`
- `material`
- `size`
- `origin_country`
- `warranty_months`
- `description`
- `tags`
- `attributes`
- `thumbnail_url`
- `status`
- `published_at`
- `created_at`
- `updated_at`

#### Enum nội bộ nên tách ra

1. `ProductStatus`
   Giá trị: `ACTIVE`, `DRAFT`, `ARCHIVED`

#### Value object nên chuẩn hóa khi chuyển sang Java

Hiện code Python đang dùng `JSONField`, nhưng để import UML đẹp hơn nên cân nhắc bóc tách:

1. `ProductDimensions`
   Gợi ý field: `length`, `width`, `height`
2. `ProductAttribute`
   Có thể chỉ để dạng generic key-value hoặc chưa cần nếu muốn skeleton đơn giản

#### DTO/API class nên có thêm

1. `ProductSummary`

### 3.3. Order Service

Nguồn chính:

- [orders/models.py](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice/e-commerce-server/order_service/orders/models.py)
- [orders/views.py](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice/e-commerce-server/order_service/orders/views.py)

#### Entity chính

1. `Order`
2. `OrderItem`

#### Thuộc tính của `Order`

- `id`
- `user_id`
- `customer_name`
- `customer_email`
- `shipping_address`
- `shipping_city`
- `status`
- `subtotal_amount`
- `shipping_fee`
- `total_amount`
- `notes`
- `metadata`
- `created_at`
- `updated_at`

#### Thuộc tính của `OrderItem`

- `id`
- `order`
- `product_id`
- `product_name`
- `sku`
- `quantity`
- `unit_price`
- `line_total`
- `product_snapshot`

#### Enum nội bộ nên tách ra

1. `OrderStatus`
   Giá trị: `PENDING`, `CONFIRMED`, `SHIPPING`, `COMPLETED`, `CANCELLED`

#### Aggregate phân tích theo DDD

1. `Order` là aggregate root
2. `OrderItem` là entity con thuộc `Order`

#### DTO/API class nên có thêm

1. `CreateOrderRequest`
2. `CreateOrderItemRequest`
3. `OrderSummary`
4. `TopCustomer`
5. `BestSellingProduct`

#### Value object nên cân nhắc

1. `ShippingInfo`
   Gom từ `shipping_address`, `shipping_city`, `shipping_fee`
2. `ProductSnapshot`
   Dùng cho `product_snapshot`

### 3.4. Payment Service

Nguồn chính:

- [payments/models.py](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice/e-commerce-server/payment_service/payments/models.py)
- [payments/views.py](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice/e-commerce-server/payment_service/payments/views.py)

#### Entity chính

1. `Payment`

Thuộc tính chính:

- `id`
- `order_id`
- `payer_name`
- `amount`
- `currency`
- `method`
- `status`
- `transaction_code`
- `gateway_response`
- `paid_at`
- `created_at`
- `updated_at`

#### Enum nội bộ nên tách ra

1. `PaymentMethod`
   Giá trị: `COD`, `BANK_TRANSFER`, `MOMO`, `CREDIT_CARD`
2. `PaymentStatus`
   Giá trị: `PENDING`, `PAID`, `FAILED`, `REFUNDED`

#### DTO/API class nên có thêm

1. `CreatePaymentRequest`
2. `PaymentSummary`

#### Value object nên cân nhắc

1. `GatewayResponse`

### 3.5. Gateway

Nguồn chính: [gateway/core/views.py](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice/e-commerce-server/gateway/core/views.py)

Gateway hiện tại không có entity nghiệp vụ mạnh, nhưng nếu muốn dựng class diagram ở mức thiết kế có thể thêm:

1. `ProxyRouter`
2. `HealthcheckResponse`
3. `ServiceRegistry`

Nhóm này phù hợp với sơ đồ kiến trúc hoặc component diagram hơn là domain class diagram.

### 3.6. AI Service

Nguồn chính: [ai_service/main.py](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice/e-commerce-server/ai_service/main.py)

#### Request/Response class đang hiện diện rõ

1. `ChatRequest`
2. `ChatResponse`
3. `SearchRequest`
4. `SearchHit`
5. `SearchResponse`
6. `TrendRequest`
7. `TrendResponse`

#### Class nghiệp vụ/phân tích logic nên đưa vào UML nếu muốn mở rộng

1. `RetrievalDoc`
2. `IntentModel`
3. `LLMProvider`
4. `Neo4jIngestionJob`

Lưu ý:

- AI service thiên về application/service class hơn là entity quan hệ.
- Nếu mục tiêu chính là import vào Visual Paradigm để vẽ domain model, có thể tách AI sang một package riêng và chỉ giữ request/response class.

### 3.7. Frontend shared types

Nguồn chính: [src/types/ecommerce.ts](/home/dezai/Documents/code/TIEU_LUAN/e-commerce-microservice/e-commerce-client/src/types/ecommerce.ts)

Frontend đang phản chiếu khá rõ các DTO backend:

1. `UserProfile`
2. `UserSummary`
3. `Product`
4. `ProductSummary`
5. `Order`
6. `OrderItem`
7. `OrderSummary`
8. `TopCustomer`
9. `BestSellingProduct`
10. `Payment`
11. `PaymentSummary`
12. `CollectionResponse<T>`
13. `DashboardData`

## 4. Quan hệ giữa các class

### 4.1. Quan hệ domain mạnh nên đưa vào UML

1. `Order` *-- `OrderItem`
   Quan hệ composition 1-n

2. `Payment` --> `Order`
   Quan hệ tham chiếu qua `order_id`

3. `Order` --> `UserProfile`
   Quan hệ tham chiếu qua `user_id`

4. `OrderItem` --> `Product`
   Quan hệ tham chiếu qua `product_id`

### 4.2. Quan hệ logic/value object nên cân nhắc

1. `Order` *-- `ShippingInfo`
2. `OrderItem` *-- `ProductSnapshot`
3. `Product` *-- `ProductDimensions`
4. `Payment` *-- `GatewayResponse`

### 4.3. Quan hệ phụ thuộc service-level

1. `OrderService` --> `UserServiceClient`
2. `OrderService` --> `ProductServiceClient`
3. `PaymentService` --> `OrderServiceClient`
4. `Gateway` --> `UserService`
5. `Gateway` --> `ProductService`
6. `Gateway` --> `OrderService`
7. `Gateway` --> `PaymentService`
8. `Gateway` --> `AIService`
9. `AIService` --> `UserService`
10. `AIService` --> `ProductService`
11. `AIService` --> `OrderService`

## 5. Những class nên ưu tiên sinh Java để import Visual Paradigm

Nếu mục tiêu là vẽ class diagram đẹp, không cần runtime, nên chia thành 3 lớp:

### 5.1. Nhóm bắt buộc

Đây là nhóm nên sinh đầu tiên:

1. `UserProfile`
2. `Product`
3. `Order`
4. `OrderItem`
5. `Payment`

### 5.2. Nhóm enum bắt buộc

1. `UserRole`
2. `UserStatus`
3. `ProductStatus`
4. `OrderStatus`
5. `PaymentMethod`
6. `PaymentStatus`

### 5.3. Nhóm value object khuyến nghị

1. `ShippingInfo`
2. `ProductDimensions`
3. `ProductSnapshot`
4. `GatewayResponse`

### 5.4. Nhóm DTO khuyến nghị

1. `CreateOrderRequest`
2. `CreateOrderItemRequest`
3. `CreatePaymentRequest`
4. `UserSummary`
5. `ProductSummary`
6. `OrderSummary`
7. `TopCustomer`
8. `BestSellingProduct`
9. `PaymentSummary`
10. `DashboardData`
11. `CollectionResponse<T>`

### 5.5. Nhóm AI/package riêng

1. `ChatRequest`
2. `ChatResponse`
3. `SearchRequest`
4. `SearchHit`
5. `SearchResponse`
6. `TrendRequest`
7. `TrendResponse`

## 6. Đề xuất package Java để import vào Visual Paradigm

Đề xuất cấu trúc package:

```text
com.ecommerce.diagram.user
com.ecommerce.diagram.product
com.ecommerce.diagram.order
com.ecommerce.diagram.payment
com.ecommerce.diagram.shared
com.ecommerce.diagram.ai
com.ecommerce.diagram.gateway
```

Trong đó:

- `user`: entity + enum + summary của user
- `product`: entity + enum + value object của product
- `order`: entity + enum + request/summary của order
- `payment`: entity + enum + request/summary của payment
- `shared`: `CollectionResponse`, `DashboardData`
- `ai`: request/response class của AI
- `gateway`: class mô tả proxy/gateway nếu cần

## 7. Danh sách file Java đề xuất sinh ở bước tiếp theo

### 7.1. Package `com.ecommerce.diagram.user`

1. `UserProfile.java`
2. `UserRole.java`
3. `UserStatus.java`
4. `UserSummary.java`
5. `UserLoginRequest.java`
6. `UserLoginResponse.java`

### 7.2. Package `com.ecommerce.diagram.product`

1. `Product.java`
2. `ProductStatus.java`
3. `ProductDimensions.java`
4. `ProductSummary.java`

### 7.3. Package `com.ecommerce.diagram.order`

1. `Order.java`
2. `OrderItem.java`
3. `OrderStatus.java`
4. `ShippingInfo.java`
5. `ProductSnapshot.java`
6. `CreateOrderRequest.java`
7. `CreateOrderItemRequest.java`
8. `OrderSummary.java`
9. `TopCustomer.java`
10. `BestSellingProduct.java`

### 7.4. Package `com.ecommerce.diagram.payment`

1. `Payment.java`
2. `PaymentMethod.java`
3. `PaymentStatus.java`
4. `GatewayResponse.java`
5. `CreatePaymentRequest.java`
6. `PaymentSummary.java`

### 7.5. Package `com.ecommerce.diagram.shared`

1. `CollectionResponse.java`
2. `DashboardData.java`

### 7.6. Package `com.ecommerce.diagram.ai`

1. `ChatRequest.java`
2. `ChatResponse.java`
3. `SearchRequest.java`
4. `SearchHit.java`
5. `SearchResponse.java`
6. `TrendRequest.java`
7. `TrendResponse.java`

### 7.7. Package `com.ecommerce.diagram.gateway`

1. `ProxyRouter.java`
2. `HealthcheckResponse.java`
3. `ServiceRegistry.java`

## 8. Chiến lược sinh Java để import Visual Paradigm

### Phương án khuyến nghị

Sinh Java theo kiểu `POJO-only`, tức là:

- Chỉ khai báo package
- Class
- Field
- Enum
- Quan hệ object/list
- Constructor rỗng
- Getter/setter cơ bản nếu cần

Không cần:

- Logic nghiệp vụ
- Annotation JPA
- Annotation Spring
- Method xử lý phức tạp

Lý do:

- Visual Paradigm chỉ cần cấu trúc class đủ rõ để reverse code ra class diagram.
- Giữ skeleton mỏng sẽ ít lỗi import hơn.

## 9. Thứ tự thực hiện ở bước code tiếp theo

Kế hoạch sinh file Java nên làm theo 3 đợt:

1. Đợt 1: sinh domain core
   `UserProfile`, `Product`, `Order`, `OrderItem`, `Payment` và toàn bộ enum

2. Đợt 2: sinh value object + DTO tổng hợp
   `ShippingInfo`, `ProductDimensions`, `GatewayResponse`, `Summary`, `DashboardData`

3. Đợt 3: sinh AI/gateway/supporting classes
   `ChatRequest`, `ChatResponse`, `SearchResponse`, `ProxyRouter`, `ServiceRegistry`

## 10. Gợi ý phạm vi UML nên vẽ

Nếu cần sơ đồ gọn và đúng trọng tâm tiểu luận, nên ưu tiên:

1. `Domain Class Diagram`
   UserProfile, Product, Order, OrderItem, Payment, các enum/value object

2. `Service Dependency Diagram`
   Gateway, User Service, Product Service, Order Service, Payment Service, AI Service

3. `AI Supporting Class Diagram`
   Chat/Search/Trend DTO + Retrieval/Provider abstraction nếu cần

## 11. Kết luận ngắn

Từ code hiện tại, các class nghiệp vụ mạnh nhất của hệ thống là:

- `UserProfile`
- `Product`
- `Order`
- `OrderItem`
- `Payment`

Trong đó:

- `Order` là aggregate root quan trọng nhất.
- `OrderItem` là entity con mạnh nhất trong toàn bộ domain model.
- `Payment` phụ thuộc logic vào `Order`.
- `Shipping` và `Cart` hiện chưa phải entity độc lập trong code thực tế.

## 12. Bước tiếp theo đề xuất

Nếu bạn đồng ý, bước tiếp theo mình có thể làm luôn:

1. Sinh toàn bộ bộ file `.java` skeleton theo package ở trên để import vào Visual Paradigm.
2. Hoặc chỉ sinh bộ tối thiểu cho `Domain Class Diagram` trước để sơ đồ gọn hơn.
