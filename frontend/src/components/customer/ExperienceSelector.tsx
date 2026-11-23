"use client";

import React from "react";
import { Smile, Meh, Frown } from "lucide-react";
import { cn } from "@/lib/utils";

export type ExperienceLevel = "positive" | "neutral" | "negative";

interface ExperienceSelectorProps {
  value: ExperienceLevel;
  onChange: (value: ExperienceLevel) => void;
}

export function ExperienceSelector({ value, onChange }: ExperienceSelectorProps) {
  const options: Array<{
    id: ExperienceLevel;
    label: string;
    icon: typeof Smile;
    selectedColor: string;
  }> = [
    {
      id: "positive",
      label: "Great Experience",
      icon: Smile,
      selectedColor: "border-emerald-500 bg-emerald-50/70 text-emerald-800",
    },
    {
      id: "neutral",
      label: "Okay / Neutral",
      icon: Meh,
      selectedColor: "border-amber-500 bg-amber-50/70 text-amber-800",
    },
    {
      id: "negative",
      label: "Needs Improvement",
      icon: Frown,
      selectedColor: "border-rose-500 bg-rose-50/70 text-rose-800",
    },
  ];

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-slate-800 block">
        Overall Visit Experience <span className="text-emerald-600">*</span>
      </label>
      <div className="grid grid-cols-3 gap-2.5">
        {options.map((opt) => {
          const Icon = opt.icon;
          const isSelected = value === opt.id;
          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => onChange(opt.id)}
              className={cn(
                "flex flex-col items-center justify-center p-3 sm:p-4 rounded-2xl border transition-all text-center focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500",
                isSelected
                  ? opt.selectedColor + " font-semibold ring-1 ring-emerald-500/20 shadow-xs"
                  : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
              )}
            >
              <Icon className={cn("w-6 h-6 sm:w-7 sm:h-7 mb-1.5", isSelected ? "currentColor" : "text-slate-400")} />
              <span className="text-xs sm:text-sm leading-tight">{opt.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

