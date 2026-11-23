"use client";

import React from "react";
import { Check, ArrowRight, ThumbsUp, Wrench } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface StepTagsProps {
  positiveTags: string[];
  improvementTags: string[];
  onTogglePositiveTag: (tag: string) => void;
  onToggleImprovementTag: (tag: string) => void;
  onContinue: () => void;
  primaryColor?: string;
}

const POPULAR_POSITIVE_TAGS = [
  "Delicious Flavors",
  "Quick Service",
  "Attentive & Kind Staff",
  "Great Ambience",
  "Generous Portions",
  "Spotless & Clean",
  "Fresh Ingredients",
  "Excellent Drinks",
  "Good Value",
  "Welcoming Vibe",
];

const POPULAR_IMPROVEMENT_TAGS = [
  "Wait Time",
  "Food Temperature",
  "Noise Level",
  "Order Accuracy",
  "Table Cleanliness",
  "Staff Attention",
  "Portion Size",
  "Menu Variety",
];

export function StepTags({
  positiveTags,
  improvementTags,
  onTogglePositiveTag,
  onToggleImprovementTag,
  onContinue,
  primaryColor = "#16a34a",
}: StepTagsProps) {
  const totalSelected = positiveTags.length + improvementTags.length;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="space-y-1">
        <h2 className="text-xl font-bold tracking-tight text-slate-900">
          Highlights & Feedback Tags
        </h2>
        <p className="text-xs text-slate-500">
          Select any tags that describe your experience (optional). Tap to toggle.
        </p>
      </div>

      {/* Section A: Positive Highlights */}
      <div className="space-y-2.5">
        <div className="flex items-center space-x-1.5 text-xs font-bold text-emerald-800 uppercase tracking-wider">
          <ThumbsUp className="w-3.5 h-3.5 text-emerald-600" />
          <span>What made your visit great?</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {POPULAR_POSITIVE_TAGS.map((tag) => {
            const isSelected = positiveTags.includes(tag);
            return (
              <button
                key={tag}
                type="button"
                onClick={() => onTogglePositiveTag(tag)}
                className={cn(
                  "inline-flex items-center px-3.5 py-2 rounded-xl text-xs font-semibold transition-all duration-150 touch-manipulation border active:scale-95",
                  isSelected
                    ? "bg-emerald-600 text-white border-emerald-600 shadow-2xs"
                    : "bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50/70"
                )}
              >
                {isSelected && <Check className="w-3.5 h-3.5 mr-1.5 shrink-0 stroke-[2.5]" />}
                <span>{tag}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Section B: Areas for Improvement */}
      <div className="space-y-2.5 pt-2">
        <div className="flex items-center space-x-1.5 text-xs font-bold text-amber-800 uppercase tracking-wider">
          <Wrench className="w-3.5 h-3.5 text-amber-600" />
          <span>Where could we improve?</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {POPULAR_IMPROVEMENT_TAGS.map((tag) => {
            const isSelected = improvementTags.includes(tag);
            return (
              <button
                key={tag}
                type="button"
                onClick={() => onToggleImprovementTag(tag)}
                className={cn(
                  "inline-flex items-center px-3.5 py-2 rounded-xl text-xs font-semibold transition-all duration-150 touch-manipulation border active:scale-95",
                  isSelected
                    ? "bg-amber-600 text-white border-amber-600 shadow-2xs"
                    : "bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50/70"
                )}
              >
                {isSelected && <Check className="w-3.5 h-3.5 mr-1.5 shrink-0 stroke-[2.5]" />}
                <span>{tag}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Continue CTA */}
      <div className="pt-3 space-y-2">
        <Button
          type="button"
          size="lg"
          className="w-full text-base font-bold shadow-sm"
          style={{ backgroundColor: primaryColor }}
          onClick={onContinue}
        >
          <span>
            {totalSelected > 0
              ? `Continue (${totalSelected} tag${totalSelected > 1 ? "s" : ""} selected)`
              : "Continue to Remarks"}
          </span>
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>

        {totalSelected === 0 && (
          <button
            type="button"
            onClick={onContinue}
            className="w-full text-center text-xs text-slate-400 hover:text-slate-600 transition-colors py-1"
          >
            Skip this step
          </button>
        )}
      </div>
    </div>
  );
}

