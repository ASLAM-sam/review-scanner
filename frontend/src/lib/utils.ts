import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMonthName(ym: string): string {
  if (!ym || !ym.includes("-")) return ym;
  const [year, month] = ym.split("-");
  const date = new Date(parseInt(year, 10), parseInt(month, 10) - 1, 1);
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat("en-US").format(num);
}

