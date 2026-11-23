"use client";

import React, { useState } from "react";
import { StarRating } from "./StarRating";
import { Button } from "@/components/ui/Button";
import { ArrowRight, AlertCircle } from "lucide-react";

interface StepRatingsProps {
  foodRating: number;
  serviceRating: number;
  ambienceRating: number;
  onFoodChange: (val: number) => void;
  onServiceChange: (val: number) => void;
  onAmbienceChange: (val: number) => void;
  onContinue: () => void;
  primaryColor?: string;
}

export function StepRatings({
  foodRating,
  serviceRating,
  ambienceRating,
  onFoodChange,
  onServiceChange,
  onAmbienceChange,
  onContinue,
  primaryColor = "#16a34a",
}: StepRatingsProps) {
  const [showValidation, setShowValidation] = useState(false);

  const isFoodValid = foodRating >= 1 && foodRating <= 5;
  const isServiceValid = serviceRating >= 1 && serviceRating <= 5;
  const isAmbienceValid = ambienceRating >= 1 && ambienceRating <= 5;
  const isAllValid = isFoodValid && isServiceValid && isAmbienceValid;

  const handleNext = () => {
    if (!isAllValid) {
      setShowValidation(true);
      return;
    }
    setShowValidation(false);
    onContinue();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="space-y-1">
        <h2 className="text-xl font-bold tracking-tight text-slate-900">
          Rate Your Experience
        </h2>
        <p className="text-xs text-slate-500">
          Please rate each category (1 to 5 stars). Tap a star to score.
        </p>
      </div>

      {showValidation && !isAllValid && (
        <div className="flex items-start space-x-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs font-medium animate-in fade-in duration-200">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>
            Please select a rating (1 to 5 stars) for all 3 categories before proceeding.
          </span>
        </div>
      )}

      <div className="space-y-3">
        {/* Category 1: Food Quality */}
        <StarRating
          label="Food & Drinks Quality"
          description="Taste, temperature, presentation, and drink preparation"
          value={foodRating}
          onChange={(val) => {
            onFoodChange(val);
            if (showValidation) setShowValidation(false);
          }}
          hasError={showValidation && !isFoodValid}
          accentColor={primaryColor}
        />

        {/* Category 2: Service Quality */}
        <StarRating
          label="Service & Staff"
          description="Attentiveness, friendliness, and prompt hospitality"
          value={serviceRating}
          onChange={(val) => {
            onServiceChange(val);
            if (showValidation) setShowValidation(false);
          }}
          hasError={showValidation && !isServiceValid}
          accentColor={primaryColor}
        />

        {/* Category 3: Ambience */}
        <StarRating
          label="Atmosphere & Ambience"
          description="Cleanliness, dining comfort, music, and lighting"
          value={ambienceRating}
          onChange={(val) => {
            onAmbienceChange(val);
            if (showValidation) setShowValidation(false);
          }}
          hasError={showValidation && !isAmbienceValid}
          accentColor={primaryColor}
        />
      </div>

      <div className="pt-2">
        <Button
          type="button"
          size="lg"
          className="w-full text-base font-bold shadow-sm"
          style={{ backgroundColor: primaryColor }}
          onClick={handleNext}
        >
          <span>Continue to Highlights</span>
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

