/**
 * Shared TypeScript Type Definitions
 */

export interface PublicRestaurantInfo {
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  google_review_url: string;
  contact_phone?: string;
  contact_email?: string;
  address?: string;
  is_active: boolean;
  subscription_status?: string;
}

export interface RestaurantAdminInfo extends PublicRestaurantInfo {
  id?: string;
  qr_destination_url: string;
  created_at?: string;
  updated_at?: string;
}

export interface RestaurantUpdatePayload {
  name?: string;
  description?: string;
  logo_url?: string;
  primary_color?: string;
  secondary_color?: string;
  google_review_url?: string;
  qr_destination_url?: string;
  contact_phone?: string;
  contact_email?: string;
  address?: string;
}

export interface QRScanResult {
  session_id: string;
  destination_url: string;
  subscription_status: 'active' | 'expired' | 'trial' | 'suspended';
  restaurant_name: string;
  restaurant_slug: string;
}

export interface QRDetails {
  slug: string;
  destination_url: string;
  qr_svg: string;
  qr_data_url: string;
}

export interface FeedbackSubmissionPayload {
  session_id: string;
  food_rating: number; // 1-5
  service_rating: number; // 1-5
  ambience_rating: number; // 1-5
  overall_experience: 'positive' | 'neutral' | 'negative';
  positive_tags?: string[];
  improvement_tags?: string[];
  selected_prompts?: string[];
  customer_notes?: string;
}

export interface FeedbackPrompt {
  id: string;
  category: string;
  category_name: string;
  text: string;
  language: string;
  sentiment: 'positive' | 'neutral' | 'improvement';
  is_active: boolean;
}

export interface PromptCategory {
  key: string;
  name: string;
  count: number;
}

export interface FeedbackSubmissionResult {
  id?: string;
  session_id: string;
  overall_experience: string;
  created_at: string;
  google_review_prompt_eligible: boolean;
}

export interface MonthlyActivityItem {
  month: string; // YYYY-MM
  scans: number;
  feedbacks: number;
  review_clicks: number;
}

export interface AnalyticsSummary {
  total_scans: number;
  total_feedback_submissions: number;
  total_review_link_clicks: number;
  raw_scans: number;
}

export interface MonthlyActivityData {
  period: string;
  timezone: string;
  months: MonthlyActivityItem[];
}

export interface DashboardAnalytics {
  summary: AnalyticsSummary;
  monthly_activity: MonthlyActivityData;
  generated_at: string;
}

export interface AnalyticsOverview {
  total_qr_scans: number;
  total_feedback_submissions: number;
  google_review_link_clicks: number;
  monthly_activity: MonthlyActivityItem[];
  raw_qr_scans?: number;
}

export interface AdminUser {
  id?: string;
  username: string;
  full_name?: string;
  is_active: boolean;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface APIEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface SubscriptionStatus {
  status: 'active' | 'expired' | 'inactive' | 'pending' | 'cancelled';
  plan_id: string;
  plan_name: string;
  amount_paise: number;
  amount_display: string;
  currency: string;
  billing_interval: string;
  started_at?: string;
  current_period_start?: string;
  current_period_end?: string;
  expires_at: string;
  remaining_days: number;
  is_expired: boolean;
  can_renew: boolean;
}

export interface CreateOrderResult {
  order_id: string;
  amount_paise: number;
  currency: string;
  key_id: string;
  restaurant_name: string;
  plan_name: string;
  payment_id: string;
}

export interface VerifyPaymentPayload {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface VerifyPaymentResult {
  success: boolean;
  status: string;
  subscription_status: string;
  expires_at: string;
  message: string;
}

export interface PaymentHistoryItem {
  payment_id: string;
  amount_paise: number;
  amount_display: string;
  currency: string;
  status: string;
  provider_order_id: string;
  provider_payment_id?: string;
  created_at: string;
  verified_at?: string;
}

export interface PaymentHistoryResult {
  payments: PaymentHistoryItem[];
  total: number;
}
