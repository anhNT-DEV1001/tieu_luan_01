# Que Commerce Client

Giao diện Next.js + Tailwind CSS cho demo `e-commerce-server`. Client render dashboard chuyên nghiệp và gọi toàn bộ feature backend hiện có:

- tổng quan users / products / orders / payments
- tìm kiếm catalog
- tạo order mới từ user + product có sẵn
- tạo payment cho order qua gateway
- refresh live data từ backend

## Run

Đảm bảo backend đang chạy ở `http://127.0.0.1:8000` hoặc chỉnh biến môi trường `ECOMMERCE_API_BASE_URL`.

```bash
cp .env.example .env.local
npm run dev
```

Mở `http://localhost:3000`.

## Env

```bash
ECOMMERCE_API_BASE_URL=http://127.0.0.1:8000
```

## Notes

- UI thao tác từ browser qua route handler `/api/backend/*` để tránh CORS.
- SSR initial load lấy dữ liệu trực tiếp từ gateway backend.
- Backend Docker demo hiện expose gateway ở `8000` và PostgreSQL ở `5433`.
- Khi chạy trong Docker Compose của server, client tự dùng `http://ecommerce-gateway:8000`.

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
