export type UserRole = "admin" | "customer" | "staff";
export type PaymentMethod = "momo" | "cod" | "bank_transfer" | "credit_card";

export interface UserProfile {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  role: UserRole;
  status: string;
  loyalty_points: number;
  address: string;
  city: string;
  country: string;
  avatar_url: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface UserSummary {
  service: string;
  total_users: number;
  roles: Record<string, number>;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  slug: string;
  category: string;
  brand: string;
  price: number;
  discount_price: number | null;
  current_price: number;
  currency: string;
  stock_quantity: number;
  safety_stock: number;
  rating: number;
  weight_grams: number;
  dimensions: Record<string, number>;
  color: string;
  material: string;
  size: string;
  origin_country: string;
  warranty_months: number;
  description: string;
  tags: string[];
  attributes: Record<string, unknown>;
  thumbnail_url: string;
  status: string;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductSummary {
  service: string;
  total_products: number;
  average_rating: number;
  categories: string[];
}

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  product_snapshot: Record<string, unknown>;
}

export interface Order {
  id: number;
  user_id: number;
  customer_name: string;
  customer_email: string;
  shipping_address: string;
  shipping_city: string;
  status: string;
  subtotal_amount: number;
  shipping_fee: number;
  total_amount: number;
  notes: string;
  metadata: Record<string, unknown>;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface OrderSummary {
  service: string;
  total_orders: number;
  gross_revenue: number;
  top_customer: {
    user_id: number;
    customer_name: string;
    customer_email: string;
    order_count: number;
    total_spent: number;
  } | null;
  best_selling_product: {
    product_id: number;
    product_name: string;
    sku: string;
    total_quantity: number;
    total_revenue: number;
  } | null;
}

export interface Payment {
  id: number;
  order_id: number;
  payer_name: string;
  amount: number;
  currency: string;
  method: PaymentMethod;
  status: string;
  transaction_code: string;
  gateway_response: Record<string, unknown>;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentSummary {
  service: string;
  total_payments: number;
  processed_amount: number;
}

export interface CollectionResponse<T> {
  count: number;
  results: T[];
}

export interface DashboardData {
  users: UserProfile[];
  userSummary: UserSummary;
  products: Product[];
  productSummary: ProductSummary;
  orders: Order[];
  orderSummary: OrderSummary;
  payments: Payment[];
  paymentSummary: PaymentSummary;
}
