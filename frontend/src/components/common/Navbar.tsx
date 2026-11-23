"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, QrCode, Settings, LogOut, UtensilsCrossed, CreditCard } from "lucide-react";
import { removeStoredToken } from "@/lib/auth";
import { cn } from "@/lib/utils";

interface NavbarProps {
  restaurantName?: string;
}

export function Navbar({ restaurantName = "Restaurant Admin" }: NavbarProps) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await removeStoredToken();
    router.push("/admin/login");
  };

  const navLinks = [
    { href: "/admin/dashboard", label: "Analytics", icon: BarChart3 },
    { href: "/admin/qr", label: "QR Code", icon: QrCode },
    { href: "/admin/subscription", label: "Subscription", icon: CreditCard },
    { href: "/admin/settings", label: "Settings", icon: Settings },
  ];

  return (
    <header className="border-b border-slate-100 bg-white sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 pr-1">
            <div className="w-8 h-8 sm:w-9 sm:h-9 shrink-0 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
              <UtensilsCrossed className="w-4 h-4 sm:w-5 sm:h-5" />
            </div>
            <div className="min-w-0 truncate">
              <span className="font-semibold text-slate-900 block leading-tight text-xs sm:text-sm truncate max-w-[110px] sm:max-w-xs">{restaurantName}</span>
              <span className="text-[10px] sm:text-xs text-slate-500 block truncate">Feedback & Review</span>
            </div>
          </div>

          <nav className="flex items-center space-x-0.5 sm:space-x-2 shrink-0">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  title={link.label}
                  className={cn(
                    "flex items-center space-x-2 p-2 sm:px-3.5 sm:py-2 rounded-xl text-sm font-medium transition-colors",
                    isActive
                      ? "bg-emerald-50 text-emerald-700"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{link.label}</span>
                </Link>
              );
            })}

            <button
              onClick={handleLogout}
              title="Logout"
              className="flex items-center space-x-1.5 p-2 sm:px-3 sm:py-2 rounded-xl text-sm font-medium text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors ml-0.5 sm:ml-2"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}

