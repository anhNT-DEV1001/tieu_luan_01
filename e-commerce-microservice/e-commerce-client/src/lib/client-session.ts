import type { UserProfile, UserRole } from "@/types/ecommerce";

export type SessionUser = Pick<
  UserProfile,
  "id" | "full_name" | "email" | "role" | "city" | "address" | "status"
>;

const SESSION_KEY = "que-commerce-session";

export function saveSessionUser(user: SessionUser): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

export function loadSessionUser(): SessionUser | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(SESSION_KEY);
    if (!raw) return null;

    const user = JSON.parse(raw) as SessionUser;
    if (!user?.id || !user?.email || !user?.role) return null;
    return user;
  } catch {
    return null;
  }
}

export function clearSessionUser(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(SESSION_KEY);
}

export function hasRole(
  user: SessionUser | null,
  roles: UserRole[],
): user is SessionUser {
  return Boolean(user && roles.includes(user.role));
}
