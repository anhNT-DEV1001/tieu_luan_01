import type {
  CollectionResponse,
  DashboardData,
  Order,
  OrderSummary,
  Payment,
  PaymentSummary,
  Product,
  ProductSummary,
  UserProfile,
  UserSummary,
} from "@/types/ecommerce";

const backendBaseUrl =
  process.env.ECOMMERCE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${backendBaseUrl}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getDashboardData(): Promise<DashboardData> {
  const [
    userSummary,
    users,
    productSummary,
    products,
    orderSummary,
    orders,
    paymentSummary,
    payments,
  ] = await Promise.all([
    fetchJson<UserSummary>("/api/users/summary/"),
    fetchJson<CollectionResponse<UserProfile>>("/api/users/"),
    fetchJson<ProductSummary>("/api/products/summary/"),
    fetchJson<CollectionResponse<Product>>("/api/products/"),
    fetchJson<OrderSummary>("/api/orders/summary/"),
    fetchJson<CollectionResponse<Order>>("/api/orders/"),
    fetchJson<PaymentSummary>("/api/payments/summary/"),
    fetchJson<CollectionResponse<Payment>>("/api/payments/"),
  ]);

  return {
    users: users.results,
    userSummary,
    products: products.results,
    productSummary,
    orders: orders.results,
    orderSummary,
    payments: payments.results,
    paymentSummary,
  };
}

export function getEmptyDashboardData(): DashboardData {
  return {
    users: [],
    userSummary: {
      service: "user_service",
      total_users: 0,
      roles: {},
    },
    products: [],
    productSummary: {
      service: "product_service",
      total_products: 0,
      average_rating: 0,
      categories: [],
    },
    orders: [],
    orderSummary: {
      service: "order_service",
      total_orders: 0,
      gross_revenue: 0,
      top_customer: null,
      best_selling_product: null,
    },
    payments: [],
    paymentSummary: {
      service: "payment_service",
      total_payments: 0,
      processed_amount: 0,
    },
  };
}
