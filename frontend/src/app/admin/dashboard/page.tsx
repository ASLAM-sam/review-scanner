"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  QrCode,
  MessageSquare,
  MousePointerClick,
  RefreshCw,
  BarChart3,
  Table as TableIcon,
  ShieldCheck,
  Calendar,
} from "lucide-react";
import { api, APIError } from "@/lib/api";
import { isUserAuthenticated } from "@/lib/auth";
import { Navbar } from "@/components/common/Navbar";
import { MetricCard } from "@/components/admin/MetricCard";
import { MonthlyActivityChart } from "@/components/admin/MonthlyActivityChart";
import { MonthlyActivityTable } from "@/components/admin/MonthlyActivityTable";
import { DashboardSkeleton } from "@/components/admin/DashboardSkeleton";
import { ErrorAlert } from "@/components/common/ErrorAlert";
import { Button } from "@/components/ui/Button";
import type { DashboardAnalytics, RestaurantAdminInfo } from "@/types";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [restaurant, setRestaurant] = useState<RestaurantAdminInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");

  const loadDashboardData = useCallback(async (isManualRefresh = false) => {
    try {
      if (isManualRefresh) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError("");

      if (!isUserAuthenticated()) {
        router.push("/admin/login");
        return;
      }

      const [analyticsData, restaurantData] = await Promise.all([
        api.getDashboardAnalytics(),
        api.getAdminRestaurant(),
      ]);

      setAnalytics(analyticsData);
      setRestaurant(restaurantData);
      setLastRefreshedAt(new Date(analyticsData.generated_at || Date.now()));
    } catch (err) {
      if (err instanceof APIError && err.status === 401) {
        router.push("/admin/login");
      } else if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to load dashboard metrics. Please check connection and try again.");
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [router]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Format the last updated time
  const formattedLastUpdated = lastRefreshedAt
    ? lastRefreshedAt.toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      })
    : null;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar restaurantName={restaurant?.name} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Dashboard Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-200/60">
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                Dashboard
              </h1>
              {restaurant?.name && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                  {restaurant.name}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Your restaurant&apos;s QR feedback activity
            </p>
          </div>

          {/* Actions & Refresh */}
          <div className="flex items-center space-x-3 self-start sm:self-auto">
            {formattedLastUpdated && (
              <span className="text-xs text-slate-400 hidden md:inline">
                Updated at {formattedLastUpdated}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadDashboardData(true)}
              disabled={isLoading || isRefreshing}
              className="flex items-center space-x-1.5 text-xs text-slate-700 bg-white hover:bg-slate-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-emerald-600" : "text-slate-500"}`} />
              <span>{isRefreshing ? "Refreshing..." : "Refresh"}</span>
            </Button>
          </div>
        </div>

        {/* Content Area */}
        {isLoading ? (
          <DashboardSkeleton />
        ) : error ? (
          <ErrorAlert
            title="Dashboard Error"
            message={error}
            onRetry={() => loadDashboardData(false)}
          />
        ) : analytics ? (
          <div className="space-y-8">
            {/* The 3 Top-Level Business Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              {/* Metric 1: Total QR Scans */}
              <MetricCard
                title="Total QR Scans"
                value={analytics.summary.total_scans}
                icon={QrCode}
                description="Verified unique customer scans"
                subNote={
                  analytics.summary.raw_scans > analytics.summary.total_scans
                    ? `${analytics.summary.raw_scans} total hits recorded (${analytics.summary.raw_scans - analytics.summary.total_scans} bot/page reloads filtered)`
                    : "Clean count: web crawlers, bots & reloads filtered"
                }
                iconColor="text-emerald-700"
                iconBg="bg-emerald-50"
              />

              {/* Metric 2: Total Feedback Submissions */}
              <MetricCard
                title="Feedback Submissions"
                value={analytics.summary.total_feedback_submissions}
                icon={MessageSquare}
                description="Customer feedback submissions"
                subNote="Direct ratings for food, service & ambience stored privately"
                iconColor="text-blue-700"
                iconBg="bg-blue-50"
              />

              {/* Metric 3: Google Review Link Clicks */}
              <MetricCard
                title="Google Review Link Clicks"
                value={analytics.summary.total_review_link_clicks}
                icon={MousePointerClick}
                description="Tracked clicks to your review link"
                subNote="Link click tracking only. Click is not proof of a posted review (Google policy compliant)"
                iconColor="text-amber-700"
                iconBg="bg-amber-50"
              />
            </div>

            {/* Metric 4: Monthly Activity Section with View Switcher */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-xs text-slate-500">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  <span>
                    Rolling 12 calendar months &bull; Timezone:{" "}
                    <span className="font-medium text-slate-700">
                      {analytics.monthly_activity.timezone}
                    </span>
                  </span>
                </div>

                {/* View Mode Toggle */}
                <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5 shadow-xs">
                  <button
                    type="button"
                    onClick={() => setViewMode("chart")}
                    className={`flex items-center space-x-1 px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                      viewMode === "chart"
                        ? "bg-emerald-50 text-emerald-700 shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    <BarChart3 className="w-3.5 h-3.5" />
                    <span>Chart View</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode("table")}
                    className={`flex items-center space-x-1 px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                      viewMode === "table"
                        ? "bg-emerald-50 text-emerald-700 shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    <TableIcon className="w-3.5 h-3.5" />
                    <span>Table View</span>
                  </button>
                </div>
              </div>

              {/* Render Chart or Table based on mode */}
              {viewMode === "chart" ? (
                <MonthlyActivityChart
                  activity={analytics.monthly_activity.months}
                  timezone={analytics.monthly_activity.timezone}
                />
              ) : (
                <MonthlyActivityTable activity={analytics.monthly_activity.months} />
              )}
            </div>

            {/* Privacy & Compliance Footer Badge */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-white border border-slate-200/80 text-xs text-slate-500">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>
                  Single-tenant private deployment &bull; All customer feedback notes and session data are stored securely and excluded from summary analytics.
                </span>
              </div>
              <span className="text-[11px] text-slate-400 hidden sm:inline">
                Independent Instance
              </span>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}
