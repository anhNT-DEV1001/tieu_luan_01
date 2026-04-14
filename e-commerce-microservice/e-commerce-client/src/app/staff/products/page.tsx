import { ProductManagementPage } from "@/components/product-management-page";

export default function StaffProductsPage() {
  return <ProductManagementPage allowedRoles={["staff", "admin"]} title="Staff Product Manager" />;
}
