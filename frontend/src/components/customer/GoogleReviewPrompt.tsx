"use client";

import React, { useState } from "react";
import { ExternalLink, CheckCircle2, MessageSquareHeart } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { api } from "@/lib/api";

interface GoogleReviewPromptProps {
  sessionId: string;
  restaurantName: string;
  googleReviewUrl: string;
}

export function GoogleReviewPrompt({
  sessionId,
  restaurantName,
  googleReviewUrl,
}: GoogleReviewPromptProps) {
  const [hasClicked, setHasClicked] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const handleOpenGoogleReview = async () => {
    setIsRecording(true);
    try {
      // Record click asynchronously without blocking customer navigation
      await api.recordReviewClick({
        session_id: sessionId,
        target_url: googleReviewUrl,
      });
    } catch (err) {
      console.warn("Could not record review link click:", err);
    } finally {
      setIsRecording(false);
      setHasClicked(true);
      // Open official Google Review page in a new window/tab
      window.open(googleReviewUrl, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <Card className="border-emerald-100 bg-gradient-to-b from-emerald-50/40 to-white overflow-hidden">
      <CardContent className="p-6 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
          <MessageSquareHeart className="w-6 h-6" />
        </div>

        <div className="space-y-1.5">
          <h3 className="text-lg font-bold text-slate-900">
            Share Your Experience on Google
          </h3>
          <p className="text-sm text-slate-600 max-w-md mx-auto leading-relaxed">
            Would you like to support {restaurantName} by sharing your genuine thoughts publicly on Google Reviews?
          </p>
        </div>

        <div className="pt-2 max-w-sm mx-auto space-y-2">
          <Button
            size="lg"
            className="w-full bg-emerald-600 hover:bg-emerald-700 shadow-sm"
            onClick={handleOpenGoogleReview}
            isLoading={isRecording}
          >
            <span>Open Google Review Page</span>
            <ExternalLink className="w-4 h-4 ml-2" />
          </Button>

          {hasClicked && (
            <div className="flex items-center justify-center space-x-1.5 text-xs text-emerald-700 font-medium pt-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Link opened in a new tab. Thank you!</span>
            </div>
          )}
        </div>

        <p className="text-xs text-slate-400 max-w-xs mx-auto">
          Google reviews are submitted directly by you on Google&apos;s official page in accordance with Google policies.
        </p>
      </CardContent>
    </Card>
  );
}

