"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { formatMonthName, formatNumber } from "@/lib/utils";
import type { MonthlyActivityItem } from "@/types";
import { BarChart3, Info } from "lucide-react";

interface MonthlyActivityChartProps {
  activity: MonthlyActivityItem[];
  timezone?: string;
}

export function MonthlyActivityChart({ activity, timezone }: MonthlyActivityChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Compute maximum count for scaling (minimum of 5 for a clean Y axis when low/zero activity)
  const maxVal = Math.max(
    5,
    ...activity.flatMap((m) => [m.scans, m.feedbacks, m.review_clicks])
  );

  const totalEvents = activity.reduce(
    (sum, m) => sum + m.scans + m.feedbacks + m.review_clicks,
    0
  );

  // 4 Y-axis ticks
  const yTicks = [
    Math.round(maxVal),
    Math.round((maxVal * 3) / 4),
    Math.round((maxVal * 2) / 4),
    Math.round(maxVal / 4),
    0,
  ];

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-5 h-5 text-emerald-600" />
              <CardTitle>12-Month Activity Overview</CardTitle>
            </div>
            <CardDescription className="mt-1">
              Monthly breakdown of QR Scans, Feedback Submissions, and Google Review Link Clicks
              {timezone ? ` (${timezone})` : ""}.
            </CardDescription>
          </div>

          {/* Color Legend */}
          <div className="flex items-center flex-wrap gap-3 text-xs font-medium text-slate-600">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-xs bg-emerald-500 inline-block shadow-xs" />
              <span>QR Scans</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-xs bg-blue-500 inline-block shadow-xs" />
              <span>Feedback</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-xs bg-amber-500 inline-block shadow-xs" />
              <span>Review Clicks</span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {totalEvents === 0 && (
          <div className="mb-4 flex items-center gap-2 p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-600">
            <Info className="w-4 h-4 text-slate-400 shrink-0" />
            <span>
              Zero activity recorded in the past 12 months. All calendar months are preserved with zero counts.
              Activity will automatically plot here as customers scan your table QR code.
            </span>
          </div>
        )}

        {/* Chart Container */}
        <div className="relative pt-6 pb-2">
          {/* Active Hover Tooltip Card (Pinned above or floating) */}
          <div className="h-14 mb-2 flex items-center justify-between px-3 py-2 rounded-lg bg-slate-50 border border-slate-200/80 text-xs text-slate-700 transition-all">
            {hoveredIndex !== null && activity[hoveredIndex] ? (
              <>
                <div className="font-semibold text-slate-900">
                  {formatMonthName(activity[hoveredIndex].month)}:
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-emerald-700 font-medium">
                    Scans: <span className="font-bold">{formatNumber(activity[hoveredIndex].scans)}</span>
                  </span>
                  <span className="text-blue-700 font-medium">
                    Feedback: <span className="font-bold">{formatNumber(activity[hoveredIndex].feedbacks)}</span>
                  </span>
                  <span className="text-amber-700 font-medium">
                    Review Clicks: <span className="font-bold">{formatNumber(activity[hoveredIndex].review_clicks)}</span>
                  </span>
                </div>
              </>
            ) : (
              <span className="text-slate-400 italic">
                Hover over or tap any month below to inspect exact counts.
              </span>
            )}
          </div>

          {/* Grouped Bar Graph */}
          <div className="relative h-64 flex items-end">
            {/* Horizontal Grid lines */}
            <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
              {yTicks.map((tick, i) => (
                <div key={i} className="flex items-center w-full">
                  <span className="w-8 text-[10px] text-slate-400 text-right pr-2 select-none">
                    {tick}
                  </span>
                  <div className="flex-1 border-b border-slate-100" />
                </div>
              ))}
            </div>

            {/* Bars Column Wrapper */}
            <div className="relative z-10 ml-8 w-full h-full flex items-end justify-between gap-1 sm:gap-2">
              {activity.map((item, idx) => {
                const scanHeight = Math.max(2, (item.scans / maxVal) * 100);
                const feedbackHeight = Math.max(2, (item.feedbacks / maxVal) * 100);
                const clickHeight = Math.max(2, (item.review_clicks / maxVal) * 100);
                const isHovered = hoveredIndex === idx;

                const [year, month] = item.month.split("-");
                const shortLabel = new Date(parseInt(year, 10), parseInt(month, 10) - 1, 1).toLocaleDateString("en-US", {
                  month: "narrow",
                });
                const abbrevLabel = new Date(parseInt(year, 10), parseInt(month, 10) - 1, 1).toLocaleDateString("en-US", {
                  month: "short",
                });

                return (
                  <div
                    key={item.month}
                    className={`flex-1 h-full flex flex-col justify-end items-center group cursor-pointer transition-colors rounded-t-sm px-0.5 sm:px-1 ${
                      isHovered ? "bg-slate-100/70" : "hover:bg-slate-50/70"
                    }`}
                    onMouseEnter={() => setHoveredIndex(idx)}
                    onMouseLeave={() => setHoveredIndex(null)}
                    onClick={() => setHoveredIndex(idx)}
                  >
                    {/* The 3 grouped bars */}
                    <div className="w-full flex items-end justify-center gap-0.5 sm:gap-1 h-5/6">
                      {/* Scans bar */}
                      <div
                        className="w-1/3 max-w-[12px] bg-emerald-500 rounded-t-xs transition-all duration-300 group-hover:brightness-110"
                        style={{ height: `${scanHeight}%` }}
                        title={`Scans: ${item.scans}`}
                      />
                      {/* Feedback bar */}
                      <div
                        className="w-1/3 max-w-[12px] bg-blue-500 rounded-t-xs transition-all duration-300 group-hover:brightness-110"
                        style={{ height: `${feedbackHeight}%` }}
                        title={`Feedback: ${item.feedbacks}`}
                      />
                      {/* Review clicks bar */}
                      <div
                        className="w-1/3 max-w-[12px] bg-amber-500 rounded-t-xs transition-all duration-300 group-hover:brightness-110"
                        style={{ height: `${clickHeight}%` }}
                        title={`Review Clicks: ${item.review_clicks}`}
                      />
                    </div>

                    {/* Month Label */}
                    <div className="h-6 flex items-center justify-center pt-1">
                      <span className="hidden sm:inline text-[11px] font-medium text-slate-500 truncate">
                        {abbrevLabel}
                      </span>
                      <span className="sm:hidden text-[10px] font-medium text-slate-500">
                        {shortLabel}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

