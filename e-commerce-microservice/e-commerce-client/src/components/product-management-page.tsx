"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { requestBackendJson } from "@/lib/backend-client";
import { clearSessionUser, hasRole, loadSessionUser } from "@/lib/client-session";
import type { CollectionResponse, Product, UserRole } from "@/types/ecommerce";

type ProductFormState = {
  sku: string;
  name: string;
  slug: string;
  category: string;
  brand: string;
  price: string;
  stock_quantity: string;
  description: string;
};

const defaultFormState: ProductFormState = {
  sku: "",
  name: "",
  slug: "",
  category: "general",
  brand: "demo-brand",
  price: "100000",
  stock_quantity: "30",
  description: "",
};

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(amount);
}

function createSlug(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

export function ProductManagementPage({
  title,
  allowedRoles,
}: {
  title: string;
  allowedRoles: UserRole[];
}) {
  const [products, setProducts] = useState<Product[]>([]);
  const [formState, setFormState] = useState<ProductFormState>(defaultFormState);
  const [status, setStatus] = useState("Đang kiểm tra phiên đăng nhập...");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessionEmail, setSessionEmail] = useState("");
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    const user = loadSessionUser();
    if (!user || !hasRole(user, allowedRoles)) {
      setStatus(`Bạn cần đăng nhập với role: ${allowedRoles.join(", ")}.`);
      return;
    }

    setSessionEmail(user.email);
    setIsAuthorized(true);
    void requestBackendJson<CollectionResponse<Product>>("products/")
      .then((response) => {
        setProducts(response.results);
        setStatus("Sẵn sàng thêm sản phẩm.");
      })
      .catch((error) => {
        setStatus(error instanceof Error ? error.message : "Không tải được sản phẩm.");
      });
  }, [allowedRoles]);

  async function submitProduct(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      const slug = formState.slug || createSlug(formState.name);
      const sku = formState.sku || `SKU-${Date.now()}`;
      const product = await requestBackendJson<Product>("products/", {
        method: "POST",
        body: JSON.stringify({
          sku,
          name: formState.name,
          slug,
          category: formState.category,
          brand: formState.brand,
          price: Number(formState.price),
          stock_quantity: Number(formState.stock_quantity),
          description: formState.description,
          status: "active",
        }),
      });

      setProducts((current) => [product, ...current]);
      setFormState((current) => ({
        ...defaultFormState,
        category: current.category,
        brand: current.brand,
      }));
      setStatus(`Đã tạo sản phẩm #${product.id} (${product.name}).`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Không thêm được sản phẩm.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 px-4 py-8">
      <header className="flex flex-wrap items-center justify-between gap-2 rounded-3xl border border-white/15 bg-black/30 p-5">
        <div>
          <h1 className="text-2xl font-semibold text-white">{title}</h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">Đăng nhập: {sessionEmail || "N/A"}</p>
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
              setSessionEmail("");
              setIsAuthorized(false);
              setStatus("Đã đăng xuất.");
            }}
            type="button"
          >
            Logout
          </button>
        </div>
      </header>

      <p className="rounded-2xl border border-white/15 bg-black/30 px-4 py-3 text-sm">{status}</p>

      <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <form
          className="space-y-4 rounded-3xl border border-white/15 bg-black/30 p-5"
          onSubmit={submitProduct}
        >
          <h2 className="text-lg font-semibold text-white">Thêm sản phẩm mới</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1">
              <span className="text-sm text-[var(--color-muted)]">Name</span>
              <input
                className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                onChange={(event) => setFormState((current) => ({ ...current, name: event.target.value }))}
                required
                value={formState.name}
              />
            </label>
            <label className="space-y-1">
              <span className="text-sm text-[var(--color-muted)]">SKU (optional)</span>
              <input
                className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                onChange={(event) => setFormState((current) => ({ ...current, sku: event.target.value }))}
                value={formState.sku}
              />
            </label>
            <label className="space-y-1">
              <span className="text-sm text-[var(--color-muted)]">Slug (optional)</span>
              <input
                className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                onChange={(event) => setFormState((current) => ({ ...current, slug: event.target.value }))}
                value={formState.slug}
              />
            </label>
            <label className="space-y-1">
              <span className="text-sm text-[var(--color-muted)]">Category</span>
              <input
                className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                onChange={(event) => setFormState((current) => ({ ...current, category: event.target.value }))}
                required
                value={formState.category}
              />
            </label>
            <label className="space-y-1">
              <span className="text-sm text-[var(--color-muted)]">Brand</span>
              <input
                className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                onChange={(event) => setFormState((current) => ({ ...current, brand: event.target.value }))}
                required
                value={formState.brand}
              />
            </label>
            <label className="space-y-1">
              <span className="text-sm text-[var(--color-muted)]">Price (VND)</span>
              <input
                className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                min={1000}
                onChange={(event) => setFormState((current) => ({ ...current, price: event.target.value }))}
                required
                type="number"
                value={formState.price}
              />
            </label>
            <label className="space-y-1">
              <span className="text-sm text-[var(--color-muted)]">Stock</span>
              <input
                className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
                min={0}
                onChange={(event) =>
                  setFormState((current) => ({ ...current, stock_quantity: event.target.value }))
                }
                required
                type="number"
                value={formState.stock_quantity}
              />
            </label>
          </div>

          <label className="block space-y-1">
            <span className="text-sm text-[var(--color-muted)]">Description</span>
            <textarea
              className="min-h-20 w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
              onChange={(event) => setFormState((current) => ({ ...current, description: event.target.value }))}
              value={formState.description}
            />
          </label>

          <button
            className="rounded-xl bg-[var(--color-accent)] px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-70"
            disabled={!isAuthorized || isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Creating..." : "Create product"}
          </button>
        </form>

        <aside className="space-y-3 rounded-3xl border border-white/15 bg-black/30 p-5">
          <h2 className="text-lg font-semibold text-white">Sản phẩm mới nhất</h2>
          <div className="space-y-2 text-sm">
            {products.slice(0, 12).map((product) => (
              <div className="rounded-xl border border-white/10 p-3" key={product.id}>
                <p className="font-semibold text-white">{product.name}</p>
                <p className="text-[var(--color-muted)]">
                  {product.sku} - {product.brand} - {product.category}
                </p>
                <p className="text-[var(--color-muted)]">
                  {formatCurrency(product.current_price)} / stock {product.stock_quantity}
                </p>
              </div>
            ))}
          </div>
        </aside>
      </section>
    </main>
  );
}
