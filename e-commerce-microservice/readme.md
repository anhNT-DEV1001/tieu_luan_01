# E-commerce Microservice Demo

Đây là điểm chạy chính của toàn bộ dự án. Từ bây giờ bạn chỉ cần dùng `docker compose` tại thư mục gốc `e-commerce-microservice`.

## Cấu trúc thành phần

- `e-commerce-client`
  Frontend Next.js + Tailwind CSS. Hiển thị dashboard, catalog, user segments, orders, payments, và gọi backend qua route handler `/api/backend/*`.

- `e-commerce-server/gateway`
  API gateway của hệ thống. Đây là entrypoint backend duy nhất mà client gọi tới.

- `e-commerce-server/user_service`
  Quản lý user với 3 role: `admin`, `customer`, `staff`.

- `e-commerce-server/product_service`
  Quản lý catalog sản phẩm. Có sẵn hơn 10 product mẫu với nhiều trường dữ liệu.

- `e-commerce-server/order_service`
  Tạo và quản lý order. Gọi sang `user_service` và `product_service` để validate dữ liệu.

- `e-commerce-server/payment_service`
  Xử lý thanh toán demo cho order.

- `postgres`
  PostgreSQL trung tâm. Tất cả service dùng chung 1 database nhưng mỗi service có schema riêng:
  `user_service`, `product_service`, `order_service`, `payment_service`.

## Tại sao trước đây có 2 docker compose?

Lúc đầu `docker-compose.yml` nằm trong `e-commerce-server` để dựng riêng backend.
Sau đó client được thêm vào, nên phát sinh nhu cầu chạy cả frontend lẫn backend cùng lúc.
Nếu giữ cả root compose và server compose thì sẽ có 2 nguồn cấu hình, rất dễ lệch nhau.

Hiện tại tôi đã chuẩn hóa lại:

- `e-commerce-microservice/docker-compose.yaml` là compose tổng duy nhất để chạy toàn bộ hệ thống.
- File compose trong `e-commerce-server` đã được bỏ để tránh nhầm lẫn.

## Cách chạy

```bash
cd e-commerce-microservice
cp .env.example .env
docker compose up --build
```

## Cách dừng

```bash
cd e-commerce-microservice
docker compose down
```

Nếu muốn xóa luôn dữ liệu PostgreSQL đã seed:

```bash
docker compose down -v
```

## Các port mặc định

- Client: `http://localhost:3000`
- Gateway backend: `http://localhost:8000`
- PostgreSQL: `localhost:5433`

## Luồng kết nối giữa các service

1. Browser gọi `client` ở cổng `3000`.
2. Client gọi Next route handler nội bộ `/api/backend/*`.
3. Route handler trong client forward request sang `gateway`.
4. `gateway` proxy tiếp sang `user_service`, `product_service`, `order_service`, hoặc `payment_service`.
5. Các service nghiệp vụ dùng chung PostgreSQL.

## Các endpoint hữu ích

- `GET http://localhost:8000/health/`
- `GET http://localhost:8000/api/users/summary/`
- `GET http://localhost:8000/api/products/summary/`
- `GET http://localhost:8000/api/orders/summary/`
- `GET http://localhost:8000/api/payments/summary/`

## Demo thao tác nhanh

Tạo order:

```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "shipping_address": "101 Le Loi",
    "shipping_city": "Ho Chi Minh City",
    "items": [
      {"product_id": 1, "quantity": 1},
      {"product_id": 2, "quantity": 2}
    ]
  }'
```

Tạo payment:

```bash
curl -X POST http://localhost:8000/api/payments/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "method": "momo",
    "source": "gateway-demo"
  }'
```

## Ghi chú cấu hình

- Client trong Docker dùng `ECOMMERCE_API_BASE_URL=http://ecommerce-gateway:8000`
- PostgreSQL được expose ra `5433` để tránh đụng PostgreSQL local ở `5432`
- Backend service nội bộ không cần expose ra host; chỉ `client`, `gateway` và `postgres` cần port host
