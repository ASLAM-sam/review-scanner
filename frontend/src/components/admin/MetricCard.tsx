import React from "react";
import { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { formatNumber } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  description: string;
  subNote?: string;
  iconColor?: string;
  iconBg?: string;
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  subNote,
  iconColor = "text-emerald-600",
  iconBg = "bg-emerald-50",
}: MetricCardProps) {
  return (
    <Card className="hover:border-slate-200 transition-all shadow-xs flex flex-col justify-between">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-500">{title}</span>
          <div className={`w-10 h-10 rounded-xl ${iconBg} ${iconColor} flex items-center justify-center`}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-3xl font-bold tracking-tight text-slate-900">
            {formatNumber(value)}
          </div>
          <p className="mt-1 text-xs text-slate-600 font-medium">{description}</p>
          {subNote && (
            <p className="mt-1.5 text-[11px] text-slate-400 leading-normal">{subNote}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
