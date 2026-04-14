import { ProductManagementPage } from "@/components/product-management-page";

export default function AdminProductsPage() {
  return <ProductManagementPage allowedRoles={["admin"]} title="Admin Product Console" />;
}
