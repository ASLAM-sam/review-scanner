import React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";

export function DashboardSkeleton() {
  return (
    <div className="space-y-8 animate-pulse" role="status" aria-label="Loading dashboard metrics">
      {/* 3 Metric Cards Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="shadow-xs border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="h-4 w-28 bg-slate-200 rounded-md" />
                <div className="w-10 h-10 rounded-xl bg-slate-200" />
              </div>
              <div className="mt-3 space-y-2">
                <div className="h-8 w-20 bg-slate-300 rounded-md" />
                <div className="h-3 w-44 bg-slate-200 rounded-md" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Monthly Activity Chart / Table Skeleton */}
      <Card className="border-slate-200">
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="space-y-2">
              <div className="h-5 w-48 bg-slate-200 rounded-md" />
              <div className="h-4 w-72 bg-slate-100 rounded-md" />
            </div>
            <div className="flex gap-3">
              <div className="h-4 w-20 bg-slate-200 rounded-md" />
              <div className="h-4 w-20 bg-slate-200 rounded-md" />
              <div className="h-4 w-24 bg-slate-200 rounded-md" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-12 mb-4 bg-slate-100 rounded-lg" />
          <div className="h-64 flex items-end justify-between gap-2 pt-6 pb-2 px-6 bg-slate-50/50 rounded-lg">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="flex-1 flex flex-col items-center justify-end h-full gap-2">
                <div
                  className="w-full max-w-[28px] bg-slate-200 rounded-t-xs"
                  style={{ height: `${20 + ((i * 17) % 65)}%` }}
                />
                <div className="h-3 w-6 bg-slate-200 rounded-xs" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

