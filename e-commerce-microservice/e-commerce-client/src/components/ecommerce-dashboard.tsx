"use client";

import { startTransition, useDeferredValue, useState } from "react";

import { requestBackendJson } from "@/lib/backend-client";
import type {
  DashboardData,
  Order,
  PaymentMethod,
  Product,
} from "@/types/ecommerce";

type OrderLineDraft = {
  productId: number;
  quantity: number;
};

type OrderFormState = {
  userId: number;
  shippingAddress: string;
  shippingCity: string;
  notes: string;
  items: OrderLineDraft[];
};

type PaymentFormState = {
  orderId: number;
  method: PaymentMethod;
  source: string;
};

const paymentMethodOptions: { value: PaymentMethod; label: string }[] = [
  { value: "momo", label: "MoMo" },
  { value: "cod", label: "Cash on Delivery" },
  { value: "bank_transfer", label: "Bank Transfer" },
  { value: "credit_card", label: "Credit Card" },
];

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDate(value: string | null) {
  if (!value) return "Chưa có";
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

async function refreshDashboard(): Promise<DashboardData> {
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
    requestBackendJson<DashboardData["userSummary"]>("users/summary/"),
    requestBackendJson<{ results: DashboardData["users"] }>("users/"),
    requestBackendJson<DashboardData["productSummary"]>("products/summary/"),
    requestBackendJson<{ results: DashboardData["products"] }>("products/"),
    requestBackendJson<DashboardData["orderSummary"]>("orders/summary/"),
    requestBackendJson<{ results: DashboardData["orders"] }>("orders/"),
    requestBackendJson<DashboardData["paymentSummary"]>("payments/summary/"),
    requestBackendJson<{ results: DashboardData["payments"] }>("payments/"),
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

export function EcommerceDashboard({ initialData }: { initialData: DashboardData }) {
  const [data, setData] = useState(initialData);
  const [productSearch, setProductSearch] = useState("");
  const [activityMessage, setActivityMessage] = useState("System ready.");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSubmittingOrder, setIsSubmittingOrder] = useState(false);
  const [isSubmittingPayment, setIsSubmittingPayment] = useState(false);
  const [orderForm, setOrderForm] = useState<OrderFormState>(() => {
    const defaultUser = initialData.users.find((user) => user.role === "customer") ?? initialData.users[0];
    const defaultProducts = initialData.products.slice(0, 2);

    return {
      userId: defaultUser?.id ?? 0,
      shippingAddress: defaultUser?.address ?? "101 Le Loi",
      shippingCity: defaultUser?.city ?? "Ho Chi Minh City",
      notes: "Ưu tiên đóng gói chống sốc",
      items: defaultProducts.map((product) => ({ productId: product.id, quantity: 1 })),
    };
  });
  const [paymentForm, setPaymentForm] = useState<PaymentFormState>(() => ({
    orderId: initialData.orders[0]?.id ?? 0,
    method: "momo",
    source: "nextjs-dashboard",
  }));

  const deferredSearch = useDeferredValue(productSearch);

  const visibleProducts = data.products.filter((product) => {
    const keyword = deferredSearch.trim().toLowerCase();
    if (!keyword) return true;
    return [product.name, product.brand, product.category, product.sku]
      .join(" ")
      .toLowerCase()
      .includes(keyword);
  });

  const selectedUser = data.users.find((user) => user.id === orderForm.userId);
  const pendingOrders = data.orders.filter((order) => order.status === "pending").length;
  const paidPayments = data.payments.filter((payment) => payment.status === "paid").length;
  const lowStockProducts = data.products.filter(
    (product) => product.stock_quantity <= Math.max(product.safety_stock, 10),
  ).length;
  const compactActivity =
    activityMessage.length > 88 ? `${activityMessage.slice(0, 85).trimEnd()}...` : activityMessage;
  const topCustomer = data.orderSummary.top_customer;
  const bestSellingProduct = data.orderSummary.best_selling_product;

  const currentOrderPreview = orderForm.items
    .map((line) => {
      const product = data.products.find((item) => item.id === line.productId);
      if (!product) return null;

      return {
        product,
        quantity: line.quantity,
        lineTotal: product.current_price * line.quantity,
      };
    })
    .filter((line): line is { product: Product; quantity: number; lineTotal: number } => Boolean(line));

  const previewSubtotal = currentOrderPreview.reduce((sum, line) => sum + line.lineTotal, 0);
  const previewShipping = currentOrderPreview.length > 0 ? 30000 : 0;
  const previewTotal = previewSubtotal + previewShipping;

  async function syncDashboard(message: string) {
    setIsRefreshing(true);

    try {
      const nextData = await refreshDashboard();
      startTransition(() => {
        setData(nextData);
        setPaymentForm((current) => ({
          ...current,
          orderId: current.orderId || nextData.orders[0]?.id || 0,
        }));
        setActivityMessage(message);
      });
    } catch (error) {
      setActivityMessage(error instanceof Error ? error.message : "Could not refresh dashboard.");
    } finally {
      setIsRefreshing(false);
    }
  }

  async function handleOrderSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmittingOrder(true);

    try {
      const payload = {
        user_id: orderForm.userId,
        shipping_address: orderForm.shippingAddress,
        shipping_city: orderForm.shippingCity,
        notes: orderForm.notes,
        items: orderForm.items.map((item) => ({
          product_id: item.productId,
          quantity: item.quantity,
        })),
      };

      const order = await requestBackendJson<Order>("orders/", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setPaymentForm((current) => ({
        ...current,
        orderId: order.id,
      }));
      await syncDashboard(`Order #${order.id} created for ${order.customer_name}.`);
    } catch (error) {
      setActivityMessage(error instanceof Error ? error.message : "Could not create order.");
    } finally {
      setIsSubmittingOrder(false);
    }
  }

  async function handlePaymentSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmittingPayment(true);

    try {
      const payment = await requestBackendJson<{ id: number; order_id: number }>("payments/", {
        method: "POST",
        body: JSON.stringify({
          order_id: paymentForm.orderId,
          method: paymentForm.method,
          source: paymentForm.source,
        }),
      });

      await syncDashboard(`Payment #${payment.id} captured for order #${payment.order_id}.`);
    } catch (error) {
      setActivityMessage(error instanceof Error ? error.message : "Could not capture payment.");
    } finally {
      setIsSubmittingPayment(false);
    }
  }

  function updateOrderItem(index: number, patch: Partial<OrderLineDraft>) {
    setOrderForm((current) => ({
      ...current,
      items: current.items.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item,
      ),
    }));
  }

  function addOrderLine() {
    const nextProduct = data.products.find(
      (product) => !orderForm.items.some((item) => item.productId === product.id),
    );

    if (!nextProduct) return;

    setOrderForm((current) => ({
      ...current,
      items: [...current.items, { productId: nextProduct.id, quantity: 1 }],
    }));
  }

  function removeOrderLine(index: number) {
    setOrderForm((current) => ({
      ...current,
      items: current.items.filter((_, itemIndex) => itemIndex !== index),
    }));
  }

  return (
    <main className="dashboard-grid min-h-screen">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8">
        <section className="glass-panel stat-card overflow-hidden rounded-[2rem] border border-[var(--color-line)]">
          <div className="grid gap-8 px-6 py-8 lg:grid-cols-[1.35fr_0.95fr] lg:px-8">
            <div className="space-y-6">
              <div className="flex flex-wrap items-center gap-3">
                <span className="section-title rounded-full border border-[var(--color-line)] bg-white/5 px-3 py-1 text-[11px] text-[var(--color-muted)]">
                  Next.js + Tailwind Control Room
                </span>
                <span className="rounded-full bg-[var(--color-accent)]/12 px-3 py-1 font-mono text-xs text-[var(--color-accent)]">
                  Backend live on gateway :8000
                </span>
              </div>
              <div className="max-w-3xl space-y-4">
                <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
                  Professional e-commerce cockpit for products, customers, orders and payments.
                </h1>
                <p className="max-w-2xl text-base leading-7 text-[var(--color-muted)] sm:text-lg">
                  Giao diện này nối trực tiếp vào `e-commerce-server` qua gateway, tổng hợp toàn bộ
                  tính năng backend hiện có và cho phép tạo đơn hàng, thanh toán, theo dõi tồn kho
                  và phân khúc người dùng trên cùng một màn hình.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  className="rounded-full bg-[var(--color-accent)] px-5 py-3 text-sm font-semibold text-slate-950 transition hover:translate-y-[-1px]"
                  onClick={() => {
                    void syncDashboard("Dashboard refreshed from gateway.");
                  }}
                  type="button"
                >
                  {isRefreshing ? "Refreshing..." : "Refresh Live Data"}
                </button>
                <a
                  className="rounded-full border border-[var(--color-line)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/6"
                  href="http://127.0.0.1:8000/health/"
                  rel="noreferrer"
                  target="_blank"
                >
                  Open Gateway Health
                </a>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {[
                {
                  label: "Catalog Scale",
                  value: data.productSummary.total_products,
                  detail: `${data.productSummary.categories.length} categories`,
                },
                {
                  label: "User Base",
                  value: data.userSummary.total_users,
                  detail: `${data.userSummary.roles.customer ?? 0} customers`,
                },
                {
                  label: "Pending Orders",
                  value: pendingOrders,
                  detail: `${formatCurrency(data.orderSummary.gross_revenue)} gross revenue`,
                },
                {
                  label: "Paid Payments",
                  value: paidPayments,
                  detail: `${formatCurrency(data.paymentSummary.processed_amount)} processed`,
                },
              ].map((stat) => (
                <article
                  className="stat-card rounded-[1.6rem] border border-[var(--color-line)] bg-[var(--color-panel-strong)] p-5"
                  key={stat.label}
                >
                  <p className="section-title text-[11px] text-[var(--color-muted)]">{stat.label}</p>
                  <p className="mt-4 text-4xl font-semibold text-white">{stat.value}</p>
                  <p className="mt-2 text-sm text-[var(--color-muted)]">{stat.detail}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-4">
          {[
            {
              title: "Average Rating",
              value: data.productSummary.average_rating.toFixed(2),
              caption: "Across all seeded products",
            },
            {
              title: "Low Stock Watch",
              value: lowStockProducts,
              caption: "Products at or below safety threshold",
            },
            {
              title: "Top Customer",
              value: topCustomer ? topCustomer.customer_name : "N/A",
              caption: topCustomer
                ? `${topCustomer.order_count} orders • ${formatCurrency(topCustomer.total_spent)}`
                : "No customer data yet",
            },
            {
              title: "Best Seller",
              value: bestSellingProduct ? bestSellingProduct.product_name : "N/A",
              caption: bestSellingProduct
                ? `${bestSellingProduct.total_quantity} units • ${bestSellingProduct.sku}`
                : "No product sales yet",
            },
            {
              title: "Command Feed",
              value: "Live",
              caption: compactActivity,
            },
          ].map((item) => (
            <article
              className="stat-card rounded-[1.5rem] border border-[var(--color-line)] bg-[var(--color-panel)] p-5"
              key={item.title}
            >
              <p className="section-title text-[11px] text-[var(--color-muted)]">{item.title}</p>
              <p className="mt-3 text-3xl font-semibold text-white">{item.value}</p>
              <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">{item.caption}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-6">
            <article className="stat-card rounded-[1.8rem] border border-[var(--color-line)] bg-[var(--color-panel)] p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="section-title text-[11px] text-[var(--color-muted)]">Product Catalog</p>
                  <h2 className="mt-2 text-2xl font-semibold text-white">Bảng điều khiển sản phẩm</h2>
                </div>
                <input
                  className="w-full rounded-full border border-[var(--color-line)] bg-white/4 px-4 py-3 text-sm outline-none placeholder:text-[var(--color-muted)] md:max-w-xs"
                  onChange={(event) => setProductSearch(event.target.value)}
                  placeholder="Tìm theo tên, thương hiệu, SKU..."
                  value={productSearch}
                />
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                {visibleProducts.slice(0, 8).map((product) => (
                  <article
                    className="rounded-[1.4rem] border border-[var(--color-line)] bg-black/10 p-4 transition hover:border-[var(--color-accent)]/35 hover:bg-black/15"
                    key={product.id}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-lg font-semibold text-white">{product.name}</p>
                        <p className="mt-1 text-sm text-[var(--color-muted)]">
                          {product.brand} • {product.category}
                        </p>
                      </div>
                      <span className="rounded-full bg-[var(--color-accent)]/12 px-3 py-1 font-mono text-xs text-[var(--color-accent)]">
                        {product.sku}
                      </span>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-[var(--color-muted)]">
                      <span className="rounded-full border border-[var(--color-line)] px-2 py-1">
                        {product.size}
                      </span>
                      <span className="rounded-full border border-[var(--color-line)] px-2 py-1">
                        {product.material}
                      </span>
                      <span className="rounded-full border border-[var(--color-line)] px-2 py-1">
                        {product.stock_quantity} units
                      </span>
                    </div>
                    <div className="mt-5 flex items-end justify-between">
                      <div>
                        <p className="text-xl font-semibold text-white">
                          {formatCurrency(product.current_price)}
                        </p>
                        <p className="text-xs text-[var(--color-muted)]">
                          Rating {product.rating.toFixed(1)} / Warranty {product.warranty_months}m
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-[var(--color-accent-soft)]">{product.color}</p>
                        <p className="text-xs text-[var(--color-muted)]">{product.origin_country}</p>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </article>

            <article className="stat-card rounded-[1.8rem] border border-[var(--color-line)] bg-[var(--color-panel)] p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="section-title text-[11px] text-[var(--color-muted)]">Customer Segments</p>
                  <h2 className="mt-2 text-2xl font-semibold text-white">User matrix</h2>
                </div>
                <span className="rounded-full bg-white/5 px-3 py-2 font-mono text-xs text-[var(--color-muted)]">
                  3 roles active
                </span>
              </div>
              <div className="mt-5 grid gap-4 md:grid-cols-3">
                {(["admin", "staff", "customer"] as const).map((role) => {
                  const roleUsers = data.users.filter((user) => user.role === role);

                  return (
                    <div
                      className="rounded-[1.4rem] border border-[var(--color-line)] bg-black/10 p-4"
                      key={role}
                    >
                      <div className="flex items-center justify-between">
                        <p className="section-title text-[11px] text-[var(--color-muted)]">{role}</p>
                        <span className="text-sm font-semibold text-white">{roleUsers.length}</span>
                      </div>
                      <div className="mt-4 space-y-3">
                        {roleUsers.map((user) => (
                          <div
                            className="rounded-2xl border border-white/6 bg-white/4 px-3 py-3"
                            key={user.id}
                          >
                            <p className="font-semibold text-white">{user.full_name}</p>
                            <p className="mt-1 text-sm text-[var(--color-muted)]">{user.email}</p>
                            <p className="mt-2 text-xs text-[var(--color-accent)]">
                              {user.city} • {user.loyalty_points} pts
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-5 rounded-[1.4rem] border border-[var(--color-line)] bg-black/10 p-4">
                <p className="section-title text-[11px] text-[var(--color-muted)]">Potential customer</p>
                <div className="mt-3 flex flex-col gap-2">
                  <p className="text-lg font-semibold text-white">
                    {topCustomer ? topCustomer.customer_name : "Chưa có dữ liệu"}
                  </p>
                  <p className="text-sm text-[var(--color-muted)]">
                    {topCustomer
                      ? `${topCustomer.customer_email} • ${topCustomer.order_count} đơn hàng • ${formatCurrency(
                          topCustomer.total_spent,
                        )}`
                      : "Khách hàng có số lượng đơn hàng cao nhất sẽ xuất hiện tại đây."}
                  </p>
                </div>
              </div>
            </article>
          </div>

          <div className="space-y-6">
            <article className="stat-card rounded-[1.8rem] border border-[var(--color-line)] bg-[var(--color-panel)] p-6">
              <p className="section-title text-[11px] text-[var(--color-muted)]">Create Order</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Khởi tạo đơn hàng</h2>
              <form className="mt-5 space-y-4" onSubmit={handleOrderSubmit}>
                <label className="block space-y-2">
                  <span className="text-sm text-[var(--color-muted)]">Customer</span>
                  <select
                    className="w-full rounded-2xl border border-[var(--color-line)] bg-black/10 px-4 py-3 outline-none"
                    onChange={(event) => {
                      const nextUserId = Number(event.target.value);
                      const user = data.users.find((item) => item.id === nextUserId);
                      setOrderForm((current) => ({
                        ...current,
                        userId: nextUserId,
                        shippingAddress: user?.address ?? current.shippingAddress,
                        shippingCity: user?.city ?? current.shippingCity,
                      }));
                    }}
                    value={orderForm.userId}
                  >
                    {data.users
                      .filter((user) => user.role === "customer")
                      .map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.full_name} • {user.city}
                        </option>
                      ))}
                  </select>
                </label>

                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block space-y-2">
                    <span className="text-sm text-[var(--color-muted)]">Shipping city</span>
                    <input
                      className="w-full rounded-2xl border border-[var(--color-line)] bg-black/10 px-4 py-3 outline-none"
                      onChange={(event) =>
                        setOrderForm((current) => ({ ...current, shippingCity: event.target.value }))
                      }
                      value={orderForm.shippingCity}
                    />
                  </label>
                  <label className="block space-y-2">
                    <span className="text-sm text-[var(--color-muted)]">Shipping address</span>
                    <input
                      className="w-full rounded-2xl border border-[var(--color-line)] bg-black/10 px-4 py-3 outline-none"
                      onChange={(event) =>
                        setOrderForm((current) => ({
                          ...current,
                          shippingAddress: event.target.value,
                        }))
                      }
                      value={orderForm.shippingAddress}
                    />
                  </label>
                </div>

                <label className="block space-y-2">
                  <span className="text-sm text-[var(--color-muted)]">Notes</span>
                  <textarea
                    className="min-h-24 w-full rounded-2xl border border-[var(--color-line)] bg-black/10 px-4 py-3 outline-none"
                    onChange={(event) =>
                      setOrderForm((current) => ({ ...current, notes: event.target.value }))
                    }
                    value={orderForm.notes}
                  />
                </label>

                <div className="space-y-3">
                  {orderForm.items.map((item, index) => (
                    <div
                      className="grid gap-3 rounded-[1.3rem] border border-[var(--color-line)] bg-black/10 p-3"
                      key={`${item.productId}-${index}`}
                    >
                      <div className="grid gap-3 sm:grid-cols-[1fr_120px_44px]">
                        <select
                          className="rounded-2xl border border-[var(--color-line)] bg-white/4 px-4 py-3 outline-none"
                          onChange={(event) =>
                            updateOrderItem(index, { productId: Number(event.target.value) })
                          }
                          value={item.productId}
                        >
                          {data.products.map((product) => (
                            <option key={product.id} value={product.id}>
                              {product.name} • {formatCurrency(product.current_price)}
                            </option>
                          ))}
                        </select>
                        <input
                          className="rounded-2xl border border-[var(--color-line)] bg-white/4 px-4 py-3 outline-none"
                          min={1}
                          onChange={(event) =>
                            updateOrderItem(index, { quantity: Number(event.target.value) || 1 })
                          }
                          type="number"
                          value={item.quantity}
                        />
                        <button
                          className="rounded-2xl border border-[var(--color-line)] text-sm text-[var(--color-muted)] transition hover:bg-white/6"
                          onClick={() => removeOrderLine(index)}
                          type="button"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex gap-3">
                  <button
                    className="rounded-full border border-[var(--color-line)] px-4 py-2 text-sm text-[var(--color-muted)] transition hover:bg-white/6"
                    onClick={addOrderLine}
                    type="button"
                  >
                    Add product line
                  </button>
                </div>

                <div className="rounded-[1.4rem] border border-[var(--color-line)] bg-black/15 p-4">
                  <div className="flex items-center justify-between text-sm text-[var(--color-muted)]">
                    <span>Customer profile</span>
                    <span>{selectedUser?.email}</span>
                  </div>
                  <div className="mt-4 space-y-2 text-sm">
                    {currentOrderPreview.map((line) => (
                      <div className="flex items-center justify-between" key={line.product.id}>
                        <span className="text-[var(--color-muted)]">
                          {line.product.name} × {line.quantity}
                        </span>
                        <span className="font-semibold text-white">{formatCurrency(line.lineTotal)}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 space-y-2 border-t border-[var(--color-line)] pt-4">
                    <div className="flex items-center justify-between text-sm text-[var(--color-muted)]">
                      <span>Subtotal</span>
                      <span>{formatCurrency(previewSubtotal)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-[var(--color-muted)]">
                      <span>Shipping</span>
                      <span>{formatCurrency(previewShipping)}</span>
                    </div>
                    <div className="flex items-center justify-between text-base font-semibold text-white">
                      <span>Total</span>
                      <span>{formatCurrency(previewTotal)}</span>
                    </div>
                  </div>
                </div>

                <button
                  className="w-full rounded-full bg-[var(--color-accent)] px-5 py-3 text-sm font-semibold text-slate-950 transition hover:translate-y-[-1px]"
                  disabled={isSubmittingOrder}
                  type="submit"
                >
                  {isSubmittingOrder ? "Creating order..." : "Create Order via Gateway"}
                </button>
              </form>
            </article>

            <article className="stat-card rounded-[1.8rem] border border-[var(--color-line)] bg-[var(--color-panel)] p-6">
              <p className="section-title text-[11px] text-[var(--color-muted)]">Capture Payment</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Thanh toán đơn hàng</h2>
              <form className="mt-5 space-y-4" onSubmit={handlePaymentSubmit}>
                <label className="block space-y-2">
                  <span className="text-sm text-[var(--color-muted)]">Order</span>
                  <select
                    className="w-full rounded-2xl border border-[var(--color-line)] bg-black/10 px-4 py-3 outline-none"
                    onChange={(event) =>
                      setPaymentForm((current) => ({
                        ...current,
                        orderId: Number(event.target.value),
                      }))
                    }
                    value={paymentForm.orderId}
                  >
                    {data.orders.map((order) => (
                      <option key={order.id} value={order.id}>
                        #{order.id} • {order.customer_name} • {formatCurrency(order.total_amount)}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block space-y-2">
                    <span className="text-sm text-[var(--color-muted)]">Method</span>
                    <select
                      className="w-full rounded-2xl border border-[var(--color-line)] bg-black/10 px-4 py-3 outline-none"
                      onChange={(event) =>
                        setPaymentForm((current) => ({
                          ...current,
                          method: event.target.value as PaymentMethod,
                        }))
                      }
                      value={paymentForm.method}
                    >
                      {paymentMethodOptions.map((method) => (
                        <option key={method.value} value={method.value}>
                          {method.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block space-y-2">
                    <span className="text-sm text-[var(--color-muted)]">Source</span>
                    <input
                      className="w-full rounded-2xl border border-[var(--color-line)] bg-black/10 px-4 py-3 outline-none"
                      onChange={(event) =>
                        setPaymentForm((current) => ({ ...current, source: event.target.value }))
                      }
                      value={paymentForm.source}
                    />
                  </label>
                </div>

                <button
                  className="w-full rounded-full border border-[var(--color-accent)] bg-[var(--color-accent)]/10 px-5 py-3 text-sm font-semibold text-[var(--color-accent)] transition hover:bg-[var(--color-accent)]/14"
                  disabled={isSubmittingPayment}
                  type="submit"
                >
                  {isSubmittingPayment ? "Capturing payment..." : "Capture Payment"}
                </button>
              </form>

              <div className="mt-6 rounded-[1.3rem] border border-[var(--color-line)] bg-black/10 p-4">
                <p className="section-title text-[11px] text-[var(--color-muted)]">Recent payments</p>
                <div className="mt-4 space-y-3">
                  {data.payments.slice(0, 4).map((payment) => (
                    <div className="flex items-center justify-between gap-3" key={payment.id}>
                      <div>
                        <p className="font-semibold text-white">#{payment.id} • Order #{payment.order_id}</p>
                        <p className="text-sm text-[var(--color-muted)]">
                          {payment.method} • {formatDate(payment.paid_at ?? payment.created_at)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-white">{formatCurrency(payment.amount)}</p>
                        <p className="text-xs text-[var(--color-accent)]">{payment.status}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </article>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <article className="stat-card rounded-[1.8rem] border border-[var(--color-line)] bg-[var(--color-panel)] p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="section-title text-[11px] text-[var(--color-muted)]">Order Flow</p>
                <h2 className="mt-2 text-2xl font-semibold text-white">Recent orders</h2>
              </div>
              <span className="rounded-full bg-white/5 px-3 py-2 font-mono text-xs text-[var(--color-muted)]">
                {data.orders.length} orders tracked
              </span>
            </div>
            <div className="mt-5 space-y-4">
              {data.orders.map((order) => (
                <article
                  className="rounded-[1.4rem] border border-[var(--color-line)] bg-black/10 p-4"
                  key={order.id}
                >
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <p className="text-lg font-semibold text-white">
                        Order #{order.id} • {order.customer_name}
                      </p>
                      <p className="text-sm text-[var(--color-muted)]">
                        {order.shipping_city} • {order.shipping_address}
                      </p>
                      <p className="text-xs text-[var(--color-muted)]">{formatDate(order.created_at)}</p>
                    </div>
                    <div className="text-left md:text-right">
                      <p className="font-semibold text-white">{formatCurrency(order.total_amount)}</p>
                      <p className="text-sm text-[var(--color-accent)]">{order.status}</p>
                    </div>
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-[var(--color-muted)]">
                    {order.items.map((item) => (
                      <div className="flex items-center justify-between" key={item.id}>
                        <span>
                          {item.product_name} × {item.quantity}
                        </span>
                        <span>{formatCurrency(item.line_total)}</span>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </article>

          <article className="stat-card rounded-[1.8rem] border border-[var(--color-line)] bg-[var(--color-panel)] p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="section-title text-[11px] text-[var(--color-muted)]">Ops Brief</p>
                <h2 className="mt-2 text-2xl font-semibold text-white">Live command stack</h2>
              </div>
              <span className="rounded-full bg-[var(--color-accent-soft)]/14 px-3 py-2 font-mono text-xs text-[var(--color-accent-soft)]">
                Frontend synced
              </span>
            </div>

            <div className="mt-5 grid gap-4">
              <div className="rounded-[1.3rem] border border-[var(--color-line)] bg-black/10 p-4">
                <p className="section-title text-[11px] text-[var(--color-muted)]">Coverage</p>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-[var(--color-muted)]">
                  <li>Products: listing, search, pricing, stock visibility and category breadth.</li>
                  <li>Users: role segmentation for admin, staff and customer personas.</li>
                  <li>Orders: live creation from existing users and products through gateway.</li>
                  <li>Payments: capture flow against backend order records and refresh summary.</li>
                </ul>
              </div>

              <div className="rounded-[1.3rem] border border-[var(--color-line)] bg-black/10 p-4">
                <p className="section-title text-[11px] text-[var(--color-muted)]">Sales leaders</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-sm text-[var(--color-muted)]">Best selling product</p>
                    <p className="mt-1 text-lg font-semibold text-white">
                      {bestSellingProduct ? bestSellingProduct.product_name : "Chưa có dữ liệu"}
                    </p>
                    <p className="mt-1 text-sm text-[var(--color-accent)]">
                      {bestSellingProduct
                        ? `${bestSellingProduct.total_quantity} units • ${formatCurrency(
                            bestSellingProduct.total_revenue,
                          )}`
                        : "Sẽ hiển thị khi có đơn hàng."}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-[var(--color-muted)]">Potential customer</p>
                    <p className="mt-1 text-lg font-semibold text-white">
                      {topCustomer ? topCustomer.customer_name : "Chưa có dữ liệu"}
                    </p>
                    <p className="mt-1 text-sm text-[var(--color-accent)]">
                      {topCustomer
                        ? `${topCustomer.order_count} orders • ${formatCurrency(topCustomer.total_spent)}`
                        : "Sẽ hiển thị khi có lịch sử mua."}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-[1.3rem] border border-[var(--color-line)] bg-black/10 p-4">
                <p className="section-title text-[11px] text-[var(--color-muted)]">Runtime notes</p>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-[var(--color-muted)]">
                  <li>Client requests use same-origin Next route handler `/api/backend/*` to avoid CORS issues.</li>
                  <li>Server rendering fetches initial dashboard data directly from the gateway.</li>
                  <li>Default backend target can be changed with `ECOMMERCE_API_BASE_URL`.</li>
                  <li>Dashboard keeps the latest order selected for quick payment capture.</li>
                </ul>
              </div>

              <div className="rounded-[1.3rem] border border-[var(--color-line)] bg-[linear-gradient(135deg,rgba(217,255,102,0.08),rgba(240,141,73,0.12))] p-4">
                <p className="section-title text-[11px] text-[var(--color-muted)]">System pulse</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-sm text-[var(--color-muted)]">Last activity</p>
                    <p className="mt-1 text-lg font-semibold text-white">{compactActivity}</p>
                  </div>
                  <div>
                    <p className="text-sm text-[var(--color-muted)]">Client state</p>
                    <p className="mt-1 text-lg font-semibold text-white">
                      {isRefreshing ? "Refreshing" : "Stable"} / {data.orders.length} orders loaded
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}
