import React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { formatMonthName, formatNumber } from "@/lib/utils";
import type { MonthlyActivityItem } from "@/types";
import { Calendar } from "lucide-react";

interface MonthlyActivityTableProps {
  activity: MonthlyActivityItem[];
}

export function MonthlyActivityTable({ activity }: MonthlyActivityTableProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center space-x-2">
          <Calendar className="w-5 h-5 text-emerald-600" />
          <CardTitle>Monthly Activity Breakdown</CardTitle>
        </div>
        <CardDescription>
          Historical monthly volume across QR scans, customer feedback submissions, and Google Review link clicks.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {activity.length === 0 ? (
          <p className="text-sm text-slate-500 py-4 text-center">No monthly activity recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="border-b border-slate-100 bg-slate-50/70 text-xs uppercase tracking-wider text-slate-500 font-semibold">
                <tr>
                  <th scope="col" className="px-4 py-3 rounded-l-lg">Month</th>
                  <th scope="col" className="px-4 py-3 text-right">QR Scans</th>
                  <th scope="col" className="px-4 py-3 text-right">Feedback Submissions</th>
                  <th scope="col" className="px-4 py-3 text-right rounded-r-lg">Google Review Clicks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {activity.map((item) => (
                  <tr key={item.month} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-3.5 font-medium text-slate-900">
                      {formatMonthName(item.month)}
                    </td>
                    <td className="px-4 py-3.5 text-right font-medium text-slate-700">
                      {formatNumber(item.scans)}
                    </td>
                    <td className="px-4 py-3.5 text-right font-medium text-emerald-700">
                      {formatNumber(item.feedbacks)}
                    </td>
                    <td className="px-4 py-3.5 text-right font-medium text-blue-700">
                      {formatNumber(item.review_clicks)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

