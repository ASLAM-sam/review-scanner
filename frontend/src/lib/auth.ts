/**
 * Client-Side Authentication Storage Helpers
 */

import { api } from "./api";

const TOKEN_KEY = "qr_review_admin_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export async function removeStoredToken(): Promise<void> {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
  try {
    await api.logoutAdmin();
  } catch {
    // Best-effort cookie session clearance
  }
}

export function isUserAuthenticated(): boolean {
  return !!getStoredToken();
}

