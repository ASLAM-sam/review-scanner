/**
 * Typed API Client for Restaurant QR Feedback System
 */

import { getStoredToken } from "./auth";
import type {
  APIEnvelope,
  AdminUser,
  AnalyticsOverview,
  DashboardAnalytics,
  FeedbackPrompt,
  FeedbackSubmissionPayload,
  FeedbackSubmissionResult,
  LoginResult,
  PromptCategory,
  PublicRestaurantInfo,
  QRDetails,
  QRScanResult,
  RestaurantAdminInfo,
  RestaurantUpdatePayload,
  SubscriptionStatus,
  CreateOrderResult,
  VerifyPaymentPayload,
  VerifyPaymentResult,
  PaymentHistoryResult,
} from "../types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class APIError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "APIError";
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Inject token if authenticated
  const token = getStoredToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    credentials: "include",
    headers,
  });

  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}`;
    try {
      const errJson = await response.json();
      errorMessage = errJson.message || errJson.detail || errorMessage;
    } catch {
      // Ignore JSON parse failure
    }
    throw new APIError(errorMessage, response.status);
  }

  const envelope: APIEnvelope<T> = await response.json();
  return envelope.data;
}

export const api = {
  // Public customer interface
  getPublicRestaurant: (slug?: string): Promise<PublicRestaurantInfo> => {
    const query = slug ? `?slug=${encodeURIComponent(slug)}` : "";
    return request<PublicRestaurantInfo>(`/public/restaurant${query}`);
  },

  recordQRScan: (payload: { session_id?: string; referrer?: string } = {}): Promise<QRScanResult> => {
    return request<QRScanResult>("/public/qr/scan", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  submitFeedback: (payload: FeedbackSubmissionPayload): Promise<FeedbackSubmissionResult> => {
    return request<FeedbackSubmissionResult>("/public/feedback", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  recordReviewClick: (payload: { session_id: string; target_url?: string }): Promise<{ target_url: string }> => {
    return request<{ target_url: string }>("/public/review-click", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getFeedbackPrompts: (params: {
    category?: string;
    sentiment?: string;
    language?: string;
    limit?: number;
    exclude_ids?: string;
  } = {}): Promise<FeedbackPrompt[]> => {
    const searchParams = new URLSearchParams();
    if (params.category) searchParams.set("category", params.category);
    if (params.sentiment) searchParams.set("sentiment", params.sentiment);
    if (params.language) searchParams.set("language", params.language);
    if (params.limit) searchParams.set("limit", params.limit.toString());
    if (params.exclude_ids) searchParams.set("exclude_ids", params.exclude_ids);

    const qs = searchParams.toString();
    return request<FeedbackPrompt[]>(`/public/prompts${qs ? `?${qs}` : ""}`);
  },

  getPromptCategories: (language: string = "en"): Promise<PromptCategory[]> => {
    return request<PromptCategory[]>(`/public/prompts/categories?language=${encodeURIComponent(language)}`);
  },

  // Admin authentication
  loginAdmin: (payload: { email: string; password: string }): Promise<LoginResult> => {
    return request<LoginResult>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getCurrentAdmin: (): Promise<AdminUser> => {
    return request<AdminUser>("/auth/me");
  },

  logoutAdmin: (): Promise<{ authenticated: boolean }> => {
    return request<{ authenticated: boolean }>("/auth/logout", {
      method: "POST",
    });
  },

  // Admin management
  getAdminRestaurant: (): Promise<RestaurantAdminInfo> => {
    return request<RestaurantAdminInfo>("/admin/restaurant");
  },

  updateAdminRestaurant: (payload: RestaurantUpdatePayload): Promise<RestaurantAdminInfo> => {
    return request<RestaurantAdminInfo>("/admin/restaurant", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  getAdminQR: (): Promise<QRDetails> => {
    return request<QRDetails>("/admin/qr");
  },

  // Analytics (Minimal 4 business metrics)
  getDashboardAnalytics: (): Promise<DashboardAnalytics> => {
    return request<DashboardAnalytics>("/analytics/dashboard");
  },

  getAnalyticsOverview: (): Promise<AnalyticsOverview> => {
    return request<AnalyticsOverview>("/analytics/overview");
  },

  // Subscription & Payment Management
  getSubscriptionStatus: (): Promise<SubscriptionStatus> => {
    return request<SubscriptionStatus>("/admin/subscription");
  },

  createRenewalOrder: (payload?: { idempotency_key?: string }): Promise<CreateOrderResult> => {
    return request<CreateOrderResult>("/admin/subscription/create-order", {
      method: "POST",
      body: JSON.stringify(payload || {}),
    });
  },

  verifyPayment: (payload: VerifyPaymentPayload): Promise<VerifyPaymentResult> => {
    return request<VerifyPaymentResult>("/admin/subscription/verify-payment", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getPaymentHistory: (limit: number = 50): Promise<PaymentHistoryResult> => {
    return request<PaymentHistoryResult>(`/admin/subscription/payments?limit=${limit}`);
  },
};

