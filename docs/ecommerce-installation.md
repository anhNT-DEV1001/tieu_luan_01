# E-commerce Microservice - Installation Guide

Du an e-commerce co 2 cach chay chinh:

- chay day du bang Docker Compose.
- chay frontend local de phat trien UI nhanh hon.

## Yeu cau

- Docker 24+.
- Docker Compose v2.
- Neu chay frontend local: Node.js 20+.

## Cac thanh phan chinh

- `e-commerce-client`: frontend Next.js.
- `e-commerce-server/gateway`: API gateway.
- `e-commerce-server/user_service`: quan ly user.
- `e-commerce-server/product_service`: quan ly san pham.
- `e-commerce-server/order_service`: quan ly don hang.
- `e-commerce-server/payment_service`: xu ly thanh toan.
- `e-commerce-server/ai_service`: AI / retrieval demo.
- `postgres`: database chung.

## Cach chay day du bang Docker

1. Di vao thu muc du an.

```bash
cd /home/dezai/Documents/code/AI/tieu-luan-que/e-commerce-microservice
```

2. Tao file cau hinh local cho compose neu chua co.

```bash
cp .env.example .env
```

3. Neu muon chay frontend local, tao them file env cho client.

```bash
cp e-commerce-client/.env.example e-commerce-client/.env.local
```

4. Build va khoi dong toan bo stack.

```bash
docker compose up --build
```

5. Mo cac dich vu theo cong mac dinh.

```text
Client:   http://localhost:3000
Gateway:  http://localhost:8000
Postgres: localhost:5433
```

## Gia tri mac dinh trong `.env`

- `DB_NAME=ecommerce_demo`
- `DB_USER=postgres`
- `DB_PASSWORD=postgres`
- `DB_EXPOSE_PORT=5433`
- `CLIENT_PORT=3000`
- `GATEWAY_PORT=8000`

## Cach dung he thong

```bash
docker compose down
```

Neu muon xoa ca du lieu PostgreSQL:

```bash
docker compose down -v
```

## Chay frontend local de dev

1. Vao thu muc client.

```bash
cd /home/dezai/Documents/code/AI/tieu-luan-que/e-commerce-microservice/e-commerce-client
```

2. Tao file env local.

```bash
cp .env.example .env.local
```

3. Cai dependencies.

```bash
npm install
```

4. Chay Next.js.

```bash
npm run dev
```

5. Mo giao dien.

```text
http://localhost:3000
```

## Luu y khi dev local

- Neu frontend chay ngoai Docker, `ECOMMERCE_API_BASE_URL` nen tro ve `http://127.0.0.1:8000`.
- Neu frontend chay trong Docker Compose, client se dung `http://ecommerce-gateway:8000`.
- Compose backend dung chung mot PostgreSQL, nhung moi service co schema rieng.

