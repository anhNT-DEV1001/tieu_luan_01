import Link from "next/link";

import { EcommerceDashboard } from "@/components/ecommerce-dashboard";
import { getDashboardData, getEmptyDashboardData } from "@/lib/api";

export default async function Home() {
  let dashboardData = getEmptyDashboardData();

  try {
    dashboardData = await getDashboardData();
  } catch {
    dashboardData = getEmptyDashboardData();
  }

  return (
    <>
      <header className="mx-auto w-full max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
        <nav className="flex flex-wrap items-center gap-2 text-sm">
          <Link className="rounded-full border border-white/20 px-3 py-1.5 hover:bg-white/10" href="/">
            Dashboard
          </Link>
          <Link
            className="rounded-full border border-white/20 px-3 py-1.5 hover:bg-white/10"
            href="/customer/login"
          >
            Customer Login
          </Link>
          <Link
            className="rounded-full border border-white/20 px-3 py-1.5 hover:bg-white/10"
            href="/staff/products"
          >
            Staff Product Page
          </Link>
          <Link
            className="rounded-full border border-white/20 px-3 py-1.5 hover:bg-white/10"
            href="/admin/products"
          >
            Admin Product Page
          </Link>
        </nav>
      </header>
      <EcommerceDashboard initialData={dashboardData} />
    </>
  );
}
