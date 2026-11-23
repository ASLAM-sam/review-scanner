"use client";

import React from "react";
import { Send, Lock, Star, AlertCircle, RefreshCw, MessageSquareQuote } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";

interface StepCommentsProps {
  restaurantName: string;
  notes: string;
  onNotesChange: (val: string) => void;
  foodRating: number;
  serviceRating: number;
  ambienceRating: number;
  selectedPrompts?: string[];
  selectedTagsCount?: number;
  onSubmit: () => void;
  isSubmitting: boolean;
  submissionError?: string;
  onClearError?: () => void;
  primaryColor?: string;
}

export function StepComments({
  restaurantName,
  notes,
  onNotesChange,
  foodRating,
  serviceRating,
  ambienceRating,
  selectedPrompts = [],
  selectedTagsCount = 0,
  onSubmit,
  isSubmitting,
  submissionError,
  onClearError,
  primaryColor = "#16a34a",
}: StepCommentsProps) {
  const handleAppendPrompt = (promptText: string) => {
    if (notes.includes(promptText)) return;
    const separator = notes.trim().length > 0 ? " " : "";
    onNotesChange(`${notes.trim()}${separator}${promptText}`);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="space-y-1">
        <h2 className="text-xl font-bold tracking-tight text-slate-900">
          Any Additional Comments?
        </h2>
        <p className="text-xs text-slate-500">
          Share special compliments, specific dishes, or suggestions (optional).
        </p>
      </div>

      {/* Ratings Recap Banner */}
      <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-3.5 space-y-2">
        <span className="text-3xs uppercase tracking-wider font-bold text-slate-400 block">
          Your Rating Summary
        </span>
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-700">
          <span className="inline-flex items-center bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
            Food: {foodRating} <Star className="w-3 h-3 ml-1 fill-amber-400 text-amber-500" />
          </span>
          <span className="inline-flex items-center bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
            Service: {serviceRating} <Star className="w-3 h-3 ml-1 fill-amber-400 text-amber-500" />
          </span>
          <span className="inline-flex items-center bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
            Ambience: {ambienceRating} <Star className="w-3 h-3 ml-1 fill-amber-400 text-amber-500" />
          </span>
          {selectedPrompts.length > 0 && (
            <span className="inline-flex items-center bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200 text-emerald-800 font-bold">
              {selectedPrompts.length} Smart Statement{selectedPrompts.length > 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      {/* Selected Prompts Review Chips */}
      {selectedPrompts.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-2xs text-slate-500">
            <span className="font-semibold flex items-center">
              <MessageSquareQuote className="w-3 h-3 mr-1 text-emerald-600" />
              Selected Statements:
            </span>
            <span className="text-3xs text-slate-400">Tap to insert into remarks</span>
          </div>
          <div className="flex flex-col gap-1.5">
            {selectedPrompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleAppendPrompt(p)}
                className="text-left text-xs bg-emerald-50/60 border border-emerald-200/80 hover:bg-emerald-100/70 text-emerald-900 px-3 py-1.5 rounded-xl transition-colors font-medium touch-manipulation"
                title="Click to insert into remarks box"
              >
                "{p}"
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Optional Remarks Textarea */}
      <div>
        <Textarea
          label="Your Notes (Optional)"
          placeholder="e.g. The chef's special pasta was outstanding, and Marco was very welcoming..."
          value={notes}
          onChange={(e) => onNotesChange(e.target.value)}
          maxLength={1000}
          rows={4}
          helperText={`${notes.length}/1000 characters`}
        />
      </div>

      {/* Prominent Privacy Notice */}
      <div className="flex items-start space-x-3 p-3.5 bg-emerald-50/70 border border-emerald-200/80 rounded-2xl text-emerald-900">
        <div className="w-7 h-7 rounded-xl bg-emerald-100 flex items-center justify-center shrink-0 text-emerald-700 mt-0.5">
          <Lock className="w-4 h-4" />
        </div>
        <div className="space-y-0.5 text-xs">
          <p className="font-bold text-slate-900">
            Private Restaurant Feedback
          </p>
          <p className="text-slate-600 leading-relaxed">
            Your feedback goes directly and privately to {restaurantName} management.
            It is <strong className="text-slate-800">never automatically published</strong> to Google or any public site.
          </p>
        </div>
      </div>

      {/* Submission Error Banner */}
      {submissionError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-2xl space-y-2">
          <div className="flex items-start space-x-2 text-rose-800 text-xs font-medium">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <span>{submissionError}</span>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onSubmit}
            className="w-full text-xs text-rose-700 border-rose-200 hover:bg-rose-100"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Retry Submission
          </Button>
        </div>
      )}

      {/* Submit Action */}
      <div className="pt-2">
        <Button
          type="button"
          size="lg"
          className="w-full text-base font-bold shadow-sm"
          style={{ backgroundColor: primaryColor }}
          onClick={onSubmit}
          isLoading={isSubmitting}
        >
          <Send className="w-4 h-4 mr-2" />
          <span>Submit My Feedback</span>
        </Button>
      </div>
    </div>
  );
}
