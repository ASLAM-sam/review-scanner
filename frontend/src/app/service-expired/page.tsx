"use client";

import React, { useEffect, useState } from "react";
import { UtensilsCrossed, Clock, HeartHandshake } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/Card";
import type { PublicRestaurantInfo } from "@/types";

export default function ServiceExpiredPage() {
  const [restaurant, setRestaurant] = useState<PublicRestaurantInfo | null>(null);

  useEffect(() => {
    // Attempt to load basic restaurant branding safely (non-blocking)
    api
      .getPublicRestaurant()
      .then((data) => setRestaurant(data))
      .catch(() => {
        // Fallback gracefully without error display if restaurant settings cannot be fetched
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50/90 flex flex-col items-center justify-center p-4 sm:p-6">
      <Card className="max-w-md w-full border-slate-200/80 shadow-sm text-center overflow-hidden bg-white">
        {/* Subtle decorative top bar using restaurant primary color or default emerald */}
        <div
          className="h-2 w-full bg-emerald-600"
          style={{
            backgroundColor: restaurant?.primary_color || "#16a34a",
          }}
        />

        <CardContent className="p-6 sm:p-8 space-y-5">
          {/* Restaurant Logo or Icon */}
          <div className="mx-auto flex items-center justify-center">
            {restaurant?.logo_url ? (
              <img
                src={restaurant.logo_url}
                alt={restaurant.name}
                className="w-16 h-16 rounded-2xl object-cover border border-slate-100 shadow-xs"
              />
            ) : (
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-emerald-700 bg-emerald-50 border border-emerald-100"
                style={{
                  color: restaurant?.primary_color || "#16a34a",
                  backgroundColor: `${restaurant?.primary_color || "#16a34a"}12`,
                }}
              >
                <UtensilsCrossed className="w-7 h-7" />
              </div>
            )}
          </div>

          {/* Heading */}
          <div className="space-y-1.5">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              {restaurant?.name || "Digital Feedback"}
            </h1>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Service Temporarily Inactive
            </p>
          </div>

          {/* Polite Customer Message */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-xs sm:text-sm text-slate-600 leading-relaxed space-y-2">
            <p>
              Thank you for dining with us today! Our table QR feedback service is currently paused for scheduled account maintenance.
            </p>
            <p className="text-xs text-slate-500">
              We value your experience. Please feel free to share your feedback directly with your server or restaurant manager.
            </p>
          </div>

          {/* Reassurance Footer */}
          <div className="pt-2 flex items-center justify-center space-x-1.5 text-[11px] text-slate-400">
            <HeartHandshake className="w-3.5 h-3.5 text-slate-400" />
            <span>Thank you for your visit and understanding.</span>
          </div>
        </CardContent>
      </Card>

      <p className="mt-6 text-[11px] text-slate-400 text-center max-w-xs">
        Table QR codes remain permanent and will automatically reactivate once the service is renewed.
      </p>
    </div>
  );
}
