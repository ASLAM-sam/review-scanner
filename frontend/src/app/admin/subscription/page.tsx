"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Script from "next/script";
import {
  CreditCard,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  RefreshCw,
  QrCode,
  ArrowRight,
  Receipt,
  Sparkles,
} from "lucide-react";
import { api, APIError } from "@/lib/api";
import { isUserAuthenticated } from "@/lib/auth";
import { Navbar } from "@/components/common/Navbar";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorAlert } from "@/components/common/ErrorAlert";
import type {
  PaymentHistoryItem,
  RestaurantAdminInfo,
  SubscriptionStatus,
} from "@/types";

declare global {
  interface Window {
    Razorpay?: any;
  }
}

function formatDateTime(isoString?: string): string {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}

function formatDate(isoString?: string): string {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return isoString;
  }
}

export default function AdminSubscriptionPage() {
  const router = useRouter();
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [restaurant, setRestaurant] = useState<RestaurantAdminInfo | null>(null);
  const [payments, setPayments] = useState<PaymentHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const loadSubscriptionData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError("");

      if (!isUserAuthenticated()) {
        router.push("/admin/login");
        return;
      }

      const [subData, restData, historyData] = await Promise.all([
        api.getSubscriptionStatus(),
        api.getAdminRestaurant(),
        api.getPaymentHistory(20),
      ]);

      setSubscription(subData);
      setRestaurant(restData);
      setPayments(historyData.payments);
    } catch (err) {
      if (err instanceof APIError && err.status === 401) {
        router.push("/admin/login");
      } else if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to load subscription details. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadSubscriptionData();
  }, [loadSubscriptionData]);

  const handleInitiateRenewal = async () => {
    try {
      setIsProcessingPayment(true);
      setError("");
      setSuccessMessage("");

      // 1. Create order on backend (server strictly controls price of 24900 paise = ₹249)
      const idempotencyKey = `renew_${Date.now()}`;
      const order = await api.createRenewalOrder({ idempotency_key: idempotencyKey });

      // 2. Check if live Razorpay SDK is available on window
      if (typeof window !== "undefined" && window.Razorpay && order.key_id && !order.order_id.startsWith("order_mock_")) {
        const options = {
          key: order.key_id,
          amount: order.amount_paise,
          currency: order.currency,
          name: order.restaurant_name,
          description: `${order.plan_name} Renewal (1 Month)`,
          order_id: order.order_id,
          handler: async function (response: any) {
            try {
              // 3. Verify signature server-side
              const verifyResult = await api.verifyPayment({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              });
              setSuccessMessage(verifyResult.message || "Payment verified! Subscription renewed successfully.");
              await loadSubscriptionData();
            } catch (vErr: any) {
              setError(vErr.message || "Payment verification failed. Please contact support.");
            } finally {
              setIsProcessingPayment(false);
            }
          },
          modal: {
            ondismiss: function () {
              setIsProcessingPayment(false);
            },
          },
          theme: {
            color: "#16a34a",
          },
        };

        const rzp = new window.Razorpay(options);
        rzp.on("payment.failed", function (failResponse: any) {
          setError(`Payment failed: ${failResponse.error?.description || "Transaction cancelled"}`);
          setIsProcessingPayment(false);
        });
        rzp.open();
      } else {
        // Mock / Sandbox mode (when no live Razorpay keys are configured in environment)
        // Simulate immediate verified renewal for seamless testing and local evaluation
        const mockPaymentId = `pay_mock_${Date.now().toString(36)}`;
        // For testing/mock mode, compute test signature or submit verification
        // Backend mock adapter accepts test signature derived from mock secret
        const mockSig = "mock_verified_signature";
        
        // Call backend verification
        const verifyResult = await api.verifyPayment({
          razorpay_order_id: order.order_id,
          razorpay_payment_id: mockPaymentId,
          razorpay_signature: mockSig,
        });

        setSuccessMessage(verifyResult.message || "Payment verified! Subscription renewed for 1 calendar month.");
        await loadSubscriptionData();
        setIsProcessingPayment(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to initiate payment. Please try again.");
      setIsProcessingPayment(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Script
        src="https://checkout.razorpay.com/v1/checkout.js"
        strategy="lazyOnload"
      />

      <Navbar restaurantName={restaurant?.name} />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-200/60">
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                Subscription &amp; Billing
              </h1>
              {subscription && (
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    subscription.status === "active"
                      ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                      : "bg-red-50 text-red-800 border border-red-200"
                  }`}
                >
                  {subscription.status.toUpperCase()}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Manage your restaurant&apos;s monthly feedback service plan and renewal history.
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={loadSubscriptionData}
            disabled={isLoading || isProcessingPayment}
            className="self-start sm:self-auto flex items-center space-x-1.5 text-xs text-slate-700 bg-white hover:bg-slate-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-emerald-600" : "text-slate-500"}`} />
            <span>Refresh</span>
          </Button>
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-start space-x-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold">Payment Successful</p>
              <p className="text-xs text-emerald-700 mt-0.5">{successMessage}</p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <ErrorAlert
            title="Subscription Error"
            message={error}
            onRetry={loadSubscriptionData}
          />
        )}

        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner label="Loading subscription details..." />
          </div>
        ) : subscription ? (
          <div className="space-y-8">
            {/* Status & Plan Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Card 1: Current Plan */}
              <Card className="border-slate-200 shadow-xs">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Current Plan
                    </span>
                    <Sparkles className="w-4 h-4 text-emerald-600" />
                  </div>
                  <CardTitle className="text-xl mt-1 text-slate-900">
                    {subscription.plan_name}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    Single-tenant dedicated restaurant license
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-baseline space-x-1">
                    <span className="text-3xl font-extrabold text-slate-900">
                      {subscription.amount_display}
                    </span>
                    <span className="text-sm font-medium text-slate-500">
                      / {subscription.billing_interval}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Includes unlimited customer QR scans, 5-step feedback flow, and 250+ smart prompts.
                  </p>
                </CardContent>
              </Card>

              {/* Card 2: Period & Expiry */}
              <Card className="border-slate-200 shadow-xs">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Billing Period
                    </span>
                    <Clock className="w-4 h-4 text-blue-600" />
                  </div>
                  <CardTitle className="text-xl mt-1 text-slate-900">
                    {subscription.is_expired ? "Service Expired" : `${subscription.remaining_days} Days Remaining`}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    {subscription.is_expired ? "Renewal required to re-enable table feedback" : "Active until expiry timestamp"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Current Period End:</span>
                    <span className="font-semibold text-slate-900">{formatDate(subscription.expires_at)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Status:</span>
                    <span className={`font-semibold capitalize ${subscription.status === 'active' ? 'text-emerald-700' : 'text-red-700'}`}>
                      {subscription.status}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Grace Period:</span>
                    <span className="text-slate-700">0 days (exact expiry)</span>
                  </div>
                </CardContent>
              </Card>

              {/* Card 3: Renewal Action */}
              <Card className={`shadow-xs border ${subscription.is_expired ? 'border-amber-300 bg-amber-50/40' : 'border-slate-200 bg-white'}`}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Action
                    </span>
                    <CreditCard className="w-4 h-4 text-emerald-600" />
                  </div>
                  <CardTitle className="text-xl mt-1 text-slate-900">
                    {subscription.is_expired ? "Reactivate Service" : "Extend Subscription"}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    Add 1 calendar month for {subscription.amount_display}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-2">
                  <Button
                    onClick={handleInitiateRenewal}
                    disabled={isProcessingPayment}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 rounded-xl flex items-center justify-center space-x-2 shadow-xs transition-all"
                  >
                    {isProcessingPayment ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Processing Order...</span>
                      </>
                    ) : (
                      <>
                        <span>Renew for {subscription.amount_display}</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </Button>
                  <p className="mt-2 text-[11px] text-center text-slate-500">
                    Secure server-side verification &bull; Instant activation
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Permanent QR Guarantee Notice */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start space-x-3.5">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 shrink-0">
                  <QrCode className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    Permanent Table QR Code Guarantee
                  </h3>
                  <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
                    Your printed table QR codes are permanent. Renewing your subscription immediately re-activates the existing QR codes without changing the URL or requiring reprinting.
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push("/admin/qr")}
                className="shrink-0 text-xs text-slate-700"
              >
                View Table QR
              </Button>
            </div>

            {/* Payment History Audit Table */}
            <Card className="border-slate-200 shadow-xs">
              <CardHeader className="pb-3">
                <div className="flex items-center space-x-2">
                  <Receipt className="w-5 h-5 text-emerald-600" />
                  <CardTitle>Renewal &amp; Payment History</CardTitle>
                </div>
                <CardDescription className="text-xs text-slate-500">
                  Audit log of all subscription payments and renewal transactions for this establishment.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {payments.length === 0 ? (
                  <div className="py-8 text-center text-slate-400 text-xs">
                    No payment history recorded yet. When renewal payments are completed, they will be archived here.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-slate-600">
                      <thead className="border-b border-slate-100 bg-slate-50/70 uppercase tracking-wider text-[11px] font-semibold text-slate-500">
                        <tr>
                          <th className="px-4 py-3 rounded-l-lg">Date</th>
                          <th className="px-4 py-3">Order Reference</th>
                          <th className="px-4 py-3 text-right">Amount</th>
                          <th className="px-4 py-3 text-right rounded-r-lg">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {payments.map((p) => (
                          <tr key={p.payment_id} className="hover:bg-slate-50/50 transition-colors">
                            <td className="px-4 py-3 font-medium text-slate-900">
                              {formatDateTime(p.verified_at || p.created_at)}
                            </td>
                            <td className="px-4 py-3 font-mono text-[11px] text-slate-500">
                              {p.provider_order_id}
                            </td>
                            <td className="px-4 py-3 text-right font-semibold text-slate-900">
                              {p.amount_display}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                  p.status === "verified"
                                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                    : p.status === "failed"
                                    ? "bg-red-50 text-red-700 border border-red-200"
                                    : "bg-slate-100 text-slate-600"
                                }`}
                              >
                                {p.status.toUpperCase()}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        ) : null}
      </main>
    </div>
  );
}

