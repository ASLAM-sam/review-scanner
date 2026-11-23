"use client";

import React, { useState } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface StarRatingProps {
  label: string;
  description?: string;
  value: number; // 0 = unrated, 1-5 = rated
  onChange: (value: number) => void;
  required?: boolean;
  hasError?: boolean;
  accentColor?: string;
}

const RATING_DESCRIPTIONS: Record<number, { text: string; bg: string; textCol: string }> = {
  1: { text: "Poor", bg: "bg-rose-50", textCol: "text-rose-700" },
  2: { text: "Fair", bg: "bg-amber-50", textCol: "text-amber-700" },
  3: { text: "Good", bg: "bg-yellow-50", textCol: "text-yellow-700" },
  4: { text: "Very Good", bg: "bg-emerald-50", textCol: "text-emerald-700" },
  5: { text: "Excellent", bg: "bg-emerald-100", textCol: "text-emerald-800" },
};

export function StarRating({
  label,
  description,
  value,
  onChange,
  required = true,
  hasError = false,
  accentColor,
}: StarRatingProps) {
  const [hoveredStar, setHoveredStar] = useState<number | null>(null);

  const displayRating = hoveredStar !== null ? hoveredStar : value;
  const ratingInfo = displayRating > 0 ? RATING_DESCRIPTIONS[displayRating] : null;

  const handleKeyDown = (e: React.KeyboardEvent, star: number) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onChange(star);
    } else if (e.key === "ArrowRight" || e.key === "ArrowUp") {
      e.preventDefault();
      onChange(Math.min(5, (value || 0) + 1));
    } else if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
      e.preventDefault();
      onChange(Math.max(1, (value || 2) - 1));
    }
  };

  return (
    <div
      className={cn(
        "rounded-2xl p-4 transition-all duration-200 border",
        hasError
          ? "border-rose-300 bg-rose-50/40 ring-1 ring-rose-200"
          : "border-slate-100 bg-white shadow-2xs hover:border-slate-200"
      )}
    >
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1.5 mb-2.5">
        <div>
          <span className="text-sm font-bold text-slate-800 block">
            {label} {required && <span className="text-rose-500 font-semibold">*</span>}
          </span>
          {description && (
            <p className="text-xs text-slate-500 mt-0.5 leading-snug">{description}</p>
          )}
        </div>

        <div>
          {ratingInfo ? (
            <span
              className={cn(
                "inline-flex items-center text-xs font-bold px-2.5 py-0.75 rounded-full transition-colors",
                ratingInfo.bg,
                ratingInfo.textCol
              )}
            >
              {displayRating} ★ {ratingInfo.text}
            </span>
          ) : (
            <span className="text-xs text-slate-400 font-medium italic">
              Tap to rate
            </span>
          )}
        </div>
      </div>

      <div
        role="radiogroup"
        aria-label={`${label} rating out of 5 stars`}
        className="flex items-center space-x-2 touch-manipulation pt-1"
        onMouseLeave={() => setHoveredStar(null)}
      >
        {[1, 2, 3, 4, 5].map((star) => {
          const isFilled = star <= displayRating;

          return (
            <button
              key={star}
              type="button"
              role="radio"
              aria-checked={value === star}
              aria-label={`${star} star${star > 1 ? "s" : ""} - ${RATING_DESCRIPTIONS[star]?.text}`}
              onClick={() => onChange(star)}
              onMouseEnter={() => setHoveredStar(star)}
              onKeyDown={(e) => handleKeyDown(e, star)}
              className={cn(
                "min-w-[46px] min-h-[46px] p-2 flex items-center justify-center rounded-xl transition-all duration-150",
                "focus:outline-hidden focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-amber-500",
                "active:scale-90 hover:scale-110",
                isFilled ? "bg-amber-50/60" : "bg-slate-50 hover:bg-slate-100/80"
              )}
            >
              <Star
                className={cn(
                  "w-7 h-7 sm:w-8 sm:h-8 transition-colors duration-150",
                  isFilled
                    ? "fill-amber-400 text-amber-500 drop-shadow-xs"
                    : "fill-transparent text-slate-300"
                )}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}
