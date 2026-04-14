"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { requestBackendJson } from "@/lib/backend-client";
import { saveSessionUser } from "@/lib/client-session";
import type { UserProfile } from "@/types/ecommerce";

type LoginResponse = {
  user: UserProfile;
};

export default function CustomerLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("customer1@demo.local");
  const [status, setStatus] = useState("Nhập email để đăng nhập.");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await requestBackendJson<LoginResponse>("users/login/", {
        method: "POST",
        body: JSON.stringify({ email }),
      });

      saveSessionUser(response.user);
      if (response.user.role === "customer") {
        setStatus("Đăng nhập thành công. Đang chuyển đến trang đặt hàng.");
        router.push("/customer/order");
        return;
      }

      if (response.user.role === "staff") {
        setStatus("Tài khoản staff. Đang chuyển sang trang quản lý sản phẩm.");
        router.push("/staff/products");
        return;
      }

      setStatus("Tài khoản admin. Đang chuyển sang trang quản trị sản phẩm.");
      router.push("/admin/products");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Đăng nhập thất bại.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-xl flex-col justify-center px-4 py-10">
      <div className="rounded-3xl border border-white/15 bg-black/30 p-6">
        <h1 className="text-2xl font-semibold text-white">Customer Login</h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          Demo login theo email. Có thể thử `customer1@demo.local`, `staff@demo.local`, `admin@demo.local`.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="block space-y-2">
            <span className="text-sm text-[var(--color-muted)]">Email</span>
            <input
              className="w-full rounded-xl border border-white/20 bg-black/25 px-3 py-2 outline-none"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>

          <button
            className="w-full rounded-xl bg-[var(--color-accent)] px-3 py-2 font-semibold text-slate-900 disabled:opacity-70"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-4 text-sm text-[var(--color-paper)]">{status}</p>

        <div className="mt-6 flex items-center gap-2 text-sm">
          <Link className="rounded-full border border-white/20 px-3 py-1.5 hover:bg-white/10" href="/">
            Dashboard
          </Link>
          <Link
            className="rounded-full border border-white/20 px-3 py-1.5 hover:bg-white/10"
            href="/customer/order"
          >
            Customer Orders
          </Link>
        </div>
      </div>
    </main>
  );
}
