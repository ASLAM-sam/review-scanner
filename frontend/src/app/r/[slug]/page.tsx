"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { UtensilsCrossed, AlertTriangle, RefreshCw } from "lucide-react";
import { api, APIError } from "@/lib/api";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { Button } from "@/components/ui/Button";
import { FeedbackForm } from "@/components/customer/FeedbackForm";
import type { FeedbackSubmissionPayload, PublicRestaurantInfo } from "@/types";

export default function CustomerFeedbackPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params?.slug as string;

  const [restaurant, setRestaurant] = useState<PublicRestaurantInfo | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<string>("");

  const initializeFeedbackSession = async () => {
    try {
      setIsLoading(true);
      setLoadError("");

      // 1. Fetch public restaurant configuration with slug validation
      const restaurantData = await api.getPublicRestaurant(slug);
      setRestaurant(restaurantData);

      // Check subscription status immediately from restaurant metadata
      if (restaurantData.subscription_status === "expired") {
        router.push("/service-expired");
        return;
      }

      // Set dynamic page title
      if (typeof document !== "undefined" && restaurantData.name) {
        document.title = `${restaurantData.name} | Customer Feedback`;
      }

      // 2. Reuse active session from sessionStorage if the customer is refreshing the page
      const storageKey = `qr_feedback_session_${slug}`;
      const storedSession =
        typeof window !== "undefined" ? sessionStorage.getItem(storageKey) : null;

      // 3. Record scan event (passing existing session ID if reloaded to deduplicate)
      const scanResult = await api.recordQRScan({
        session_id: storedSession || undefined,
      });

      // 4. Handle expired subscription
      if (scanResult.subscription_status === "expired") {
        router.push("/service-expired");
        return;
      }

      // 5. Store session ID for subsequent refreshes
      if (typeof window !== "undefined" && scanResult.session_id) {
        sessionStorage.setItem(storageKey, scanResult.session_id);
      }

      setSessionId(scanResult.session_id);
    } catch (err) {
      if (err instanceof APIError && err.status === 404) {
        setLoadError("This restaurant was not found or is currently unavailable.");
      } else if (err instanceof APIError) {
        setLoadError(err.message);
      } else {
        setLoadError("Unable to establish a connection to the feedback system. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    initializeFeedbackSession();
  }, [slug, router]);

  const handleFeedbackSubmit = async (payload: FeedbackSubmissionPayload): Promise<boolean> => {
    try {
      setIsSubmitting(true);
      await api.submitFeedback(payload);
      return true;
    } catch (err: any) {
      if (err instanceof APIError && (err.status === 403 || err.message?.includes("SUBSCRIPTION_EXPIRED"))) {
        router.push("/service-expired");
      }
      console.error("Feedback submission error:", err);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  // State 1: Loading
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50/80 flex flex-col items-center justify-center p-4">
        <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm max-w-xs w-full text-center space-y-4">
          <LoadingSpinner size="lg" label="Preparing your dining feedback session..." />
        </div>
      </div>
    );
  }

  // State 2: Error / Unavailable Page
  if (loadError || !restaurant) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white p-7 sm:p-9 rounded-3xl border border-slate-200/90 shadow-sm max-w-sm w-full text-center space-y-4 animate-in fade-in duration-300">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
            <UtensilsCrossed className="w-7 h-7" />
          </div>

          <div className="space-y-1.5">
            <h1 className="text-xl font-bold text-slate-900">
              Restaurant Unavailable
            </h1>
            <p className="text-xs text-slate-500 leading-relaxed">
              {loadError || "We could not find active dining feedback settings for this location."}
            </p>
          </div>

          <div className="pt-2">
            <Button
              type="button"
              variant="outline"
              size="md"
              className="w-full text-xs font-semibold"
              onClick={initializeFeedbackSession}
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              Try Again
            </Button>
          </div>

          <p className="text-3xs text-slate-400">
            If you are dining with us, please notify your server or restaurant manager.
          </p>
        </div>
      </div>
    );
  }

  // State 3: Active Multi-Step Feedback Flow
  const primaryColor = restaurant.primary_color || "#16a34a";

  return (
    <div
      className="min-h-screen bg-slate-50 py-4 sm:py-8 px-3 sm:px-6"
      style={
        {
          "--brand-primary": primaryColor,
          "--brand-secondary": restaurant.secondary_color || "#15803d",
        } as React.CSSProperties
      }
    >
      <div className="max-w-md mx-auto">
        <FeedbackForm
          sessionId={sessionId}
          restaurant={restaurant}
          onSubmit={handleFeedbackSubmit}
          isSubmitting={isSubmitting}
        />
      </div>
    </div>
  );
}
