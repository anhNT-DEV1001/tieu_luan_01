"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { requestBackendJson } from "@/lib/backend-client";
import { clearSessionUser, hasRole, loadSessionUser } from "@/lib/client-session";
import type { CollectionResponse, Order, Product } from "@/types/ecommerce";

type OrderLine = {
  productId: number;
  quantity: number;
};

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(amount);
}

export default function CustomerOrderPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [shippingCity, setShippingCity] = useState("");
  const [shippingAddress, setShippingAddress] = useState("");
  const [notes, setNotes] = useState("Giao trong giờ hành chính");
  const [items, setItems] = useState<OrderLine[]>([]);
  const [status, setStatus] = useState("Đang tải dữ liệu...");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessionUserEmail, setSessionUserEmail] = useState("");
  const [sessionUserId, setSessionUserId] = useState(0);

  useEffect(() => {
    const user = loadSessionUser();
    if (!user || !hasRole(user, ["customer"])) {
      setStatus("Cần đăng nhập customer để đặt hàng.");
      return;
    }

    setSessionUserEmail(user.email);
    setSessionUserId(user.id);
    setShippingCity(user.city || "Ho Chi Minh City");
    setShippingAddress(user.address || "101 Le Loi");

    void Promise.all([
      requestBackendJson<CollectionResponse<Product>>("products/"),
      requestBackendJson<CollectionResponse<Order>>("orders/"),
    ])
      .then(([productResponse, orderResponse]) => {
        setProducts(productResponse.results);
        setOrders(orderResponse.results.filter((order) => order.user_id === user.id));
        const firstProduct = productResponse.results[0];
        setItems(firstProduct ? [{ productId: firstProduct.id, quantity: 1 }] : []);
        setStatus("Sẵn sàng tạo order.");
      })
      .catch((error) => {
        setStatus(error instanceof Error ? error.message : "Không tải được dữ liệu.");
      });
  }, []);

  const itemPreview = items
    .map((item) => {
      const product = products.find((value) => value.id === item.productId);
      if (!product) return null;
      return {
        ...item,
        product,
        total: product.current_price * item.quantity,
      };
    })
    .filter((item): item is { productId: number; quantity: number; product: Product; total: number } =>
      Boolean(item),
    );
  const subtotal = itemPreview.reduce((sum, item) => sum + item.total, 0);
  const shippingFee = itemPreview.length > 0 ? 30000 : 0;
  const grandTotal = subtotal + shippingFee;

  function updateItem(index: number, patch: Partial<OrderLine>) {
    setItems((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)),
    );
  }

  function addLine() {
    const next = products.find((product) => !items.some((item) => item.productId === product.id));
    if (!next) return;
    setItems((current) => [...current, { productId: next.id, quantity: 1 }]);
  }

  function removeLine(index: number) {
    setItems((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  async function submitOrder(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sessionUserId) return;

    setIsSubmitting(true);
    try {
      const order = await requestBackendJson<Order>("orders/", {
        method: "POST",
        body: JSON.stringify({
          user_id: sessionUserId,
          shipping_address: shippingAddress,
          shipping_city: shippingCity,
          notes,
          items: items.map((item) => ({
            product_id: item.productId,
            quantity: item.quantity,
          })),
        }),
      });

      setOrders((current) => [order, ...current]);
      setStatus(`Tạo order #${order.id} thành công.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Không tạo được order.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 px-4 py-8">
      <header className="flex flex-wrap items-center justify-between gap-2 rounded-3xl border border-white/15 bg-black/30 p-5">
        <div>
          <h1 className="text-2xl font-semibold text-white">Customer Order Portal</h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">Đăng nhập: {sessionUserEmail || "N/A"}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <Link className="rounded-full border border-white/20 px-3 py-1.5 hover:bg-white/10" href="/">
            Dashboard
          </Link>
          <Link
            className="rounded-full border border-white/20 px-3 py-1.5 hover:bg-white/10"
            href="/customer/login"
          >
            Login
          </Link>
          <button
            className="rounded-full border border-white/20 px-3 py-1.5 hover:bg-white/10"
            onClick={() => {
              clearSessionUser();
              setSessionUserEmail("");
              setSessionUserId(0);
              setStatus("Đã đăng xuất.");
            }}
            type="button"
          >
            Logout
          </button>
        </div>
      </header>

      <p className="rounded-2xl border border-white/15 bg-black/30 px-4 py-3 text-sm">{status}</p>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <form
          className="space-y-4 rounded-3xl border border-white/15 bg-black/30 p-5"
          onSubmit={submitOrder}
        >
          <h2 className="text-lg font-semibold text-white">Tạo đơn hàng mới</h2>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1">
              <span className="text-sm text-[var(--color-muted)]">Shipping city</span>
              <input
                className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                onChange={(event) => setShippingCity(event.target.value)}
                required
                value={shippingCity}
              />
            </label>
            <label className="space-y-1">
              <span className="text-sm text-[var(--color-muted)]">Shipping address</span>
              <input
                className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                onChange={(event) => setShippingAddress(event.target.value)}
                required
                value={shippingAddress}
              />
            </label>
          </div>

          <label className="space-y-1 block">
            <span className="text-sm text-[var(--color-muted)]">Notes</span>
            <textarea
              className="min-h-20 w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
              onChange={(event) => setNotes(event.target.value)}
              value={notes}
            />
          </label>

          <div className="space-y-3">
            {items.map((item, index) => (
              <div className="grid gap-2 rounded-xl border border-white/10 p-3 sm:grid-cols-[1fr_120px_44px]" key={index}>
                <select
                  className="rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                  onChange={(event) => updateItem(index, { productId: Number(event.target.value) })}
                  value={item.productId}
                >
                  {products.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.name} - {formatCurrency(product.current_price)}
                    </option>
                  ))}
                </select>
                <input
                  className="rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                  min={1}
                  onChange={(event) => updateItem(index, { quantity: Number(event.target.value) || 1 })}
                  type="number"
                  value={item.quantity}
                />
                <button
                  className="rounded-xl border border-white/20 hover:bg-white/10"
                  onClick={() => removeLine(index)}
                  type="button"
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              className="rounded-xl border border-white/20 px-3 py-2 text-sm hover:bg-white/10"
              onClick={addLine}
              type="button"
            >
              Add item
            </button>
            <button
              className="rounded-xl bg-[var(--color-accent)] px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-70"
              disabled={isSubmitting || !sessionUserId || items.length === 0}
              type="submit"
            >
              {isSubmitting ? "Creating..." : "Create order"}
            </button>
          </div>
        </form>

        <aside className="space-y-4 rounded-3xl border border-white/15 bg-black/30 p-5">
          <h2 className="text-lg font-semibold text-white">Order preview</h2>
          <div className="space-y-2 text-sm">
            {itemPreview.map((item) => (
              <div className="flex items-center justify-between" key={item.productId}>
                <span>
                  {item.product.name} × {item.quantity}
                </span>
                <span>{formatCurrency(item.total)}</span>
              </div>
            ))}
          </div>
          <div className="space-y-1 border-t border-white/10 pt-3 text-sm">
            <div className="flex items-center justify-between">
              <span>Subtotal</span>
              <span>{formatCurrency(subtotal)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Shipping</span>
              <span>{formatCurrency(shippingFee)}</span>
            </div>
            <div className="flex items-center justify-between text-base font-semibold text-white">
              <span>Total</span>
              <span>{formatCurrency(grandTotal)}</span>
            </div>
          </div>

          <h3 className="pt-2 text-base font-semibold text-white">Đơn gần đây</h3>
          <div className="space-y-2 text-sm">
            {orders.slice(0, 6).map((order) => (
              <div className="rounded-xl border border-white/10 p-3" key={order.id}>
                <p>
                  #{order.id} - {order.status}
                </p>
                <p className="text-[var(--color-muted)]">{formatCurrency(order.total_amount)}</p>
              </div>
            ))}
          </div>
        </aside>
      </section>
    </main>
  );
}
