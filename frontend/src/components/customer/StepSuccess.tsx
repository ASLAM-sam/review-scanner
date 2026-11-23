"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  ExternalLink,
  MessageSquareHeart,
  Star,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { api } from "@/lib/api";
import type { PublicRestaurantInfo } from "@/types";

interface StepSuccessProps {
  restaurant: PublicRestaurantInfo;
  sessionId: string;
  foodRating: number;
  serviceRating: number;
  ambienceRating: number;
}

export function StepSuccess({
  restaurant,
  sessionId,
  foodRating,
  serviceRating,
  ambienceRating,
}: StepSuccessProps) {
  const [hasClickedReview, setHasClickedReview] = useState(false);
  const [isRecordingClick, setIsRecordingClick] = useState(false);

  const primaryColor = restaurant.primary_color || "#16a34a";
  const googleReviewUrl = restaurant.google_review_url;

  const handleOpenGoogleReview = async () => {
    setIsRecordingClick(true);
    try {
      // Record link click event asynchronously on backend without blocking user
      await api.recordReviewClick({
        session_id: sessionId,
      });
    } catch (err) {
      console.warn("Could not record review click event:", err);
    } finally {
      setIsRecordingClick(false);
      setHasClickedReview(true);
      // Open restaurant's verified Google Review URL in a safe new window/tab
      if (googleReviewUrl) {
        window.open(googleReviewUrl, "_blank", "noopener,noreferrer");
      }
    }
  };

  return (
    <div className="space-y-6 text-center animate-in fade-in zoom-in-95 duration-400">
      {/* Success Hero Card */}
      <Card className="border-emerald-100 bg-white shadow-xs overflow-hidden">
        <CardContent className="p-7 space-y-4">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center mx-auto shadow-sm"
            style={{ backgroundColor: `${primaryColor}15`, color: primaryColor }}
          >
            <CheckCircle2 className="w-9 h-9" />
          </div>

          <div className="space-y-1.5">
            <span className="text-2xs uppercase tracking-wider font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.75 rounded-full inline-block">
              Feedback Received
            </span>
            <h2 className="text-2xl font-extrabold text-slate-900">
              Thank You!
            </h2>
            <p className="text-sm text-slate-600 max-w-sm mx-auto leading-relaxed">
              Your feedback has been sent directly to the management of{" "}
              <strong className="text-slate-900">{restaurant.name}</strong>.
              We appreciate you taking the time to help us serve you better.
            </p>
          </div>

          {/* Submitted Ratings Recap */}
          <div className="pt-2">
            <div className="inline-flex items-center gap-3 bg-slate-50 border border-slate-200/80 px-3.5 py-1.5 rounded-full text-xs font-semibold text-slate-700">
              <span>Food: {foodRating}★</span>
              <span>·</span>
              <span>Service: {serviceRating}★</span>
              <span>·</span>
              <span>Ambience: {ambienceRating}★</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Google Review Redirection Card (Always accessible to ALL customers) */}
      {googleReviewUrl && (
        <Card className="border-emerald-100 bg-gradient-to-b from-emerald-50/50 to-white shadow-xs overflow-hidden text-center">
          <CardContent className="p-6 sm:p-7 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
              <MessageSquareHeart className="w-6 h-6" />
            </div>

            <div className="space-y-1.5">
              <h3 className="text-lg font-bold text-slate-900">
                Share Your Experience on Google
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 max-w-sm mx-auto leading-relaxed">
                Would you also like to support {restaurant.name} by sharing your genuine thoughts publicly on Google Reviews?
              </p>
            </div>

            <div className="pt-1 max-w-xs mx-auto space-y-2">
              <Button
                type="button"
                size="lg"
                className="w-full text-base font-bold shadow-sm"
                style={{ backgroundColor: primaryColor }}
                onClick={handleOpenGoogleReview}
                isLoading={isRecordingClick}
              >
                <span>Open Google Review Page</span>
                <ExternalLink className="w-4 h-4 ml-2" />
              </Button>

              {hasClickedReview && (
                <div className="flex items-center justify-center space-x-1.5 text-xs text-emerald-700 font-semibold pt-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Google Review page opened in a new tab. Thank you!</span>
                </div>
              )}
            </div>

            {/* Strict Google Compliance Disclaimer */}
            <p className="text-3xs sm:text-2xs text-slate-400 max-w-xs mx-auto leading-normal pt-2">
              Google reviews are written and submitted directly by you on Google's official page in accordance with Google policies. We never auto-publish reviews or create fake ratings on your behalf.
            </p>
          </CardContent>
        </Card>
      )}

      <footer className="text-xs text-slate-400 pt-2">
        Powered by {restaurant.name} Guest Experience
      </footer>
    </div>
  );
}

