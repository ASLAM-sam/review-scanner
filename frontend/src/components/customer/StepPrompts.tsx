"use client";

import React, { useEffect, useState } from "react";
import {
  Sparkles,
  Check,
  RefreshCw,
  ArrowRight,
  Globe,
  ThumbsUp,
  Meh,
  Wrench,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { FeedbackPrompt } from "@/types";

interface StepPromptsProps {
  foodRating: number;
  serviceRating: number;
  ambienceRating: number;
  selectedPrompts: string[];
  onTogglePrompt: (promptText: string) => void;
  onContinue: () => void;
  primaryColor?: string;
}

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "te", label: "తెలుగు" },
  { code: "hi", label: "हिंदी" },
];

export function StepPrompts({
  foodRating,
  serviceRating,
  ambienceRating,
  selectedPrompts,
  onTogglePrompt,
  onContinue,
  primaryColor = "#16a34a",
}: StepPromptsProps) {
  const [language, setLanguage] = useState<string>("en");
  const [activeSentiment, setActiveSentiment] = useState<string>("all");
  const [prompts, setPrompts] = useState<FeedbackPrompt[]>([]);
  const [viewedPromptIds, setViewedPromptIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Determine initial sentiment recommendation based on ratings
  useEffect(() => {
    const avg = (foodRating + serviceRating + ambienceRating) / 3;
    if (avg >= 4) {
      setActiveSentiment("positive");
    } else if (avg <= 2.5) {
      setActiveSentiment("improvement");
    } else {
      setActiveSentiment("all");
    }
  }, [foodRating, serviceRating, ambienceRating]);

  const loadPrompts = async (resetSession: boolean = false) => {
    try {
      if (resetSession) {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }

      const excludeIdsParam = resetSession ? "" : viewedPromptIds.join(",");
      const sentimentFilter = activeSentiment === "all" ? undefined : activeSentiment;

      const results = await api.getFeedbackPrompts({
        sentiment: sentimentFilter,
        language: language,
        limit: 8,
        exclude_ids: excludeIdsParam,
      });

      // Track viewed IDs so they aren't repeated in this session
      const newIds = results.map((p) => p.id);
      setViewedPromptIds((prev) => Array.from(new Set([...prev, ...newIds])));
      setPrompts(results);
    } catch (err) {
      console.warn("Could not load smart prompts:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  // Reload when language or sentiment filter changes
  useEffect(() => {
    loadPrompts(true);
  }, [language, activeSentiment]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-800">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>Smart Experience Statements</span>
          </div>

          {/* Language Selector */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-xl text-3xs font-bold">
            <Globe className="w-3 h-3 text-slate-400 ml-1.5 mr-1" />
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => setLanguage(lang.code)}
                className={cn(
                  "px-2 py-1 rounded-lg transition-colors touch-manipulation",
                  language === lang.code
                    ? "bg-white text-slate-900 shadow-2xs font-extrabold"
                    : "text-slate-500 hover:text-slate-900"
                )}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>

        <p className="text-xs text-slate-500">
          Select any statements that best express your thoughts, or skip to write your own remarks.
        </p>
      </div>

      {/* Sentiment Filter Tabs */}
      <div className="grid grid-cols-4 gap-1.5 p-1 bg-slate-100/80 rounded-xl text-3xs sm:text-2xs font-bold">
        <button
          type="button"
          onClick={() => setActiveSentiment("all")}
          className={cn(
            "py-1.5 px-2 rounded-lg transition-all text-center touch-manipulation",
            activeSentiment === "all"
              ? "bg-white text-slate-900 shadow-2xs"
              : "text-slate-500 hover:text-slate-800"
          )}
        >
          All
        </button>
        <button
          type="button"
          onClick={() => setActiveSentiment("positive")}
          className={cn(
            "py-1.5 px-2 rounded-lg transition-all flex items-center justify-center space-x-1 touch-manipulation",
            activeSentiment === "positive"
              ? "bg-emerald-600 text-white shadow-2xs"
              : "text-emerald-700 hover:bg-emerald-50"
          )}
        >
          <ThumbsUp className="w-3 h-3 shrink-0" />
          <span>Great</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveSentiment("neutral")}
          className={cn(
            "py-1.5 px-2 rounded-lg transition-all flex items-center justify-center space-x-1 touch-manipulation",
            activeSentiment === "neutral"
              ? "bg-amber-600 text-white shadow-2xs"
              : "text-amber-700 hover:bg-amber-50"
          )}
        >
          <Meh className="w-3 h-3 shrink-0" />
          <span>Fair</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveSentiment("improvement")}
          className={cn(
            "py-1.5 px-2 rounded-lg transition-all flex items-center justify-center space-x-1 touch-manipulation",
            activeSentiment === "improvement"
              ? "bg-rose-600 text-white shadow-2xs"
              : "text-rose-700 hover:bg-rose-50"
          )}
        >
          <Wrench className="w-3 h-3 shrink-0" />
          <span>Improve</span>
        </button>
      </div>

      {/* Prompts Cards Display */}
      {isLoading ? (
        <div className="py-12">
          <LoadingSpinner size="md" label="Curating feedback prompts..." />
        </div>
      ) : prompts.length > 0 ? (
        <div className="space-y-2.5">
          <div className="grid grid-cols-1 gap-2">
            {prompts.map((p) => {
              const isSelected = selectedPrompts.includes(p.text);

              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => onTogglePrompt(p.text)}
                  className={cn(
                    "text-left p-3.5 rounded-2xl border transition-all duration-150 flex items-start space-x-3 touch-manipulation active:scale-98",
                    isSelected
                      ? "border-emerald-600 bg-emerald-50/70 text-emerald-950 ring-2 ring-emerald-600/20 shadow-xs"
                      : "border-slate-200/90 bg-white hover:border-slate-300 hover:bg-slate-50/60 text-slate-700 shadow-2xs"
                  )}
                >
                  <div
                    className={cn(
                      "w-5 h-5 rounded-lg flex items-center justify-center shrink-0 mt-0.5 transition-colors",
                      isSelected
                        ? "bg-emerald-600 text-white"
                        : "border border-slate-300 bg-slate-50"
                    )}
                  >
                    {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>

                  <div className="space-y-1 flex-1">
                    <p className="text-xs sm:text-sm font-medium leading-relaxed">
                      "{p.text}"
                    </p>
                    <span className="text-3xs font-semibold text-slate-400 block uppercase tracking-wider">
                      {p.category_name}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Shuffle / More Prompts Action */}
          <div className="flex justify-center pt-1">
            <button
              type="button"
              onClick={() => loadPrompts(false)}
              disabled={isRefreshing}
              className="inline-flex items-center text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/70 px-3 py-1.5 rounded-xl transition-all active:scale-95 touch-manipulation disabled:opacity-50"
            >
              <RefreshCw
                className={cn("w-3.5 h-3.5 mr-1.5", isRefreshing && "animate-spin")}
              />
              <span>More Statements</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-xs text-slate-500">
          No statements available for this filter.
        </div>
      )}

      {/* Navigation Actions */}
      <div className="pt-2 space-y-2">
        <Button
          type="button"
          size="lg"
          className="w-full text-base font-bold shadow-sm"
          style={{ backgroundColor: primaryColor }}
          onClick={onContinue}
        >
          <span>
            {selectedPrompts.length > 0
              ? `Continue (${selectedPrompts.length} Selected)`
              : "Continue to Remarks"}
          </span>
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>

        {selectedPrompts.length === 0 && (
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
