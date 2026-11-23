"use client";

import React from "react";
import { Utensils, Smile, Meh, Frown, ArrowRight, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import type { PublicRestaurantInfo } from "@/types";

interface StepWelcomeProps {
  restaurant: PublicRestaurantInfo;
  selectedSentiment: "positive" | "neutral" | "negative" | null;
  onSelectSentiment: (sentiment: "positive" | "neutral" | "negative") => void;
  onContinue: () => void;
}

export function StepWelcome({
  restaurant,
  selectedSentiment,
  onSelectSentiment,
  onContinue,
}: StepWelcomeProps) {
  const primaryColor = restaurant.primary_color || "#16a34a";

  const sentimentOptions = [
    {
      id: "positive" as const,
      label: "Great",
      description: "Wonderful visit",
      icon: Smile,
      badge: "★ Loved it",
      activeClass: "border-emerald-500 bg-emerald-50/80 text-emerald-900 ring-2 ring-emerald-500/20",
      iconClass: "text-emerald-600",
    },
    {
      id: "neutral" as const,
      label: "Okay",
      description: "Average visit",
      icon: Meh,
      badge: "Decent",
      activeClass: "border-amber-500 bg-amber-50/80 text-amber-900 ring-2 ring-amber-500/20",
      iconClass: "text-amber-600",
    },
    {
      id: "negative" as const,
      label: "Not Great",
      description: "Had some issues",
      icon: Frown,
      badge: "Needs work",
      activeClass: "border-rose-500 bg-rose-50/80 text-rose-900 ring-2 ring-rose-500/20",
      iconClass: "text-rose-600",
    },
  ];

  return (
    <div className="space-y-6 text-center animate-in fade-in duration-300">
      {/* Restaurant Identity */}
      <div className="space-y-3">
        {restaurant.logo_url ? (
          <img
            src={restaurant.logo_url}
            alt={restaurant.name}
            className="w-20 h-20 rounded-2xl mx-auto object-cover border-2 border-white shadow-sm ring-1 ring-slate-100"
          />
        ) : (
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center text-white mx-auto shadow-sm"
            style={{ backgroundColor: primaryColor }}
          >
            <Utensils className="w-8 h-8" />
          </div>
        )}

        <div>
          <span className="text-2xs uppercase tracking-wider font-bold text-slate-400 block mb-1">
            Welcome to
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            {restaurant.name}
          </h1>
          {restaurant.description ? (
            <p className="text-sm text-slate-600 mt-1.5 max-w-sm mx-auto leading-relaxed">
              {restaurant.description}
            </p>
          ) : (
            <p className="text-sm text-slate-500 mt-1 max-w-xs mx-auto">
              We value your thoughts. Thank you for dining with us today!
            </p>
          )}
        </div>
      </div>

      <div className="h-px bg-slate-200/70 max-w-xs mx-auto" />

      {/* Main Question */}
      <div className="space-y-2">
        <h2 className="text-lg sm:text-xl font-bold text-slate-900">
          How was your experience today?
        </h2>
        <p className="text-xs text-slate-500 max-w-xs mx-auto">
          Tap an option to begin. It takes less than 45 seconds.
        </p>
      </div>

      {/* Sentiment Selection Cards */}
      <div className="grid grid-cols-3 gap-2.5 sm:gap-3">
        {sentimentOptions.map((opt) => {
          const Icon = opt.icon;
          const isSelected = selectedSentiment === opt.id;

          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => {
                onSelectSentiment(opt.id);
              }}
              className={cn(
                "p-3 sm:p-4 rounded-2xl border transition-all duration-200 flex flex-col items-center justify-center text-center touch-manipulation",
                "focus:outline-hidden focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-emerald-500 active:scale-95",
                isSelected
                  ? opt.activeClass + " shadow-xs font-semibold"
                  : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/80 text-slate-700"
              )}
            >
              <Icon className={cn("w-7 h-7 sm:w-8 sm:h-8 mb-1.5", opt.iconClass)} />
              <span className="text-xs sm:text-sm font-bold block">{opt.label}</span>
              <span className="text-3xs sm:text-2xs text-slate-400 mt-0.5 block">
                {opt.description}
              </span>
            </button>
          );
        })}
      </div>

      {/* Continue CTA */}
      <div className="pt-2">
        <Button
          type="button"
          size="lg"
          className="w-full text-base font-bold shadow-sm"
          style={{ backgroundColor: primaryColor }}
          onClick={onContinue}
        >
          <span>Rate Your Experience</span>
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>

      {/* Privacy & No Registration Note */}
      <div className="flex items-center justify-center space-x-1.5 text-2xs text-slate-400 pt-1">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
        <span>Direct private feedback · No app or login required</span>
      </div>
    </div>
  );
}

