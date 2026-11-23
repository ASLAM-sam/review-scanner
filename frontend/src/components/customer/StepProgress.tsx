"use client";

import React from "react";
import { ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";

interface StepProgressProps {
  currentStep: number; // 1 to 4
  totalSteps?: number; // default 4
  stepTitle: string;
  onBack?: () => void;
  primaryColor?: string;
}

export function StepProgress({
  currentStep,
  totalSteps = 4,
  stepTitle,
  onBack,
  primaryColor = "#16a34a",
}: StepProgressProps) {
  const percent = Math.min(100, Math.round((currentStep / totalSteps) * 100));

  return (
    <div className="w-full space-y-3 pb-2">
      <div className="flex items-center justify-between">
        {onBack && currentStep > 1 ? (
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors p-1.5 -ml-1.5 rounded-lg active:scale-95 touch-manipulation"
            aria-label="Go to previous step"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            <span>Back</span>
          </button>
        ) : (
          <div className="w-12" />
        )}

        <div className="text-center">
          <span className="text-2xs uppercase tracking-wider font-bold text-slate-400 block">
            Step {currentStep} of {totalSteps}
          </span>
          <span className="text-xs font-bold text-slate-700">{stepTitle}</span>
        </div>

        <span className="text-xs font-bold text-slate-400 w-12 text-right">
          {percent}%
        </span>
      </div>

      {/* Progress Track */}
      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300 ease-out"
          style={{
            width: `${percent}%`,
            backgroundColor: primaryColor,
          }}
        />
      </div>
    </div>
  );
}

