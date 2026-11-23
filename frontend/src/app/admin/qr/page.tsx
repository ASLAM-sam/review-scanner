"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Download, Copy, Check, QrCode, ExternalLink, Printer } from "lucide-react";
import { api, APIError } from "@/lib/api";
import { isUserAuthenticated } from "@/lib/auth";
import { Navbar } from "@/components/common/Navbar";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorAlert } from "@/components/common/ErrorAlert";
import type { QRDetails, RestaurantAdminInfo } from "@/types";

export default function AdminQRPage() {
  const router = useRouter();
  const [qrDetails, setQRDetails] = useState<QRDetails | null>(null);
  const [restaurant, setRestaurant] = useState<RestaurantAdminInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true);
        if (!isUserAuthenticated()) {
          router.push("/admin/login");
          return;
        }

        const [qr, res] = await Promise.all([api.getAdminQR(), api.getAdminRestaurant()]);
        setQRDetails(qr);
        setRestaurant(res);
      } catch (err) {
        if (err instanceof APIError && err.status === 401) {
          router.push("/admin/login");
        } else {
          setError("Failed to load QR code assets.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [router]);

  const handleCopyLink = () => {
    if (!qrDetails?.destination_url) return;
    navigator.clipboard.writeText(qrDetails.destination_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadPNG = () => {
    if (!qrDetails?.qr_data_url) return;
    const a = document.createElement("a");
    a.href = qrDetails.qr_data_url;
    a.download = `${restaurant?.slug || "restaurant"}-qr-code.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDownloadSVG = () => {
    if (!qrDetails?.qr_svg) return;
    const blob = new Blob([qrDetails.qr_svg], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${restaurant?.slug || "restaurant"}-qr-code.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar restaurantName={restaurant?.name} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Dynamic QR Code
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Display this QR code on table tents, bill holders, counters, and take-away packaging.
          </p>
        </div>

        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner label="Generating dynamic QR assets..." />
          </div>
        ) : error ? (
          <ErrorAlert title="QR Generation Error" message={error} />
        ) : qrDetails ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Visual QR Code Display Card */}
            <Card className="border-slate-100 shadow-sm flex flex-col items-center justify-center p-8 text-center bg-white">
              <div className="p-4 bg-white rounded-3xl border-2 border-slate-100 shadow-xs mb-4">
                <img
                  src={qrDetails.qr_data_url}
                  alt={`QR Code for ${restaurant?.name}`}
                  className="w-56 h-56 rounded-xl object-contain"
                />
              </div>

              <div className="space-y-1">
                <h3 className="text-lg font-bold text-slate-900">{restaurant?.name}</h3>
                <p className="text-xs text-slate-400">Scan to launch feedback &amp; review</p>
              </div>

              <div className="flex gap-2.5 mt-6 w-full max-w-xs">
                <Button variant="outline" size="sm" className="flex-1" onClick={handleDownloadPNG}>
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  PNG (Raster)
                </Button>
                <Button variant="outline" size="sm" className="flex-1" onClick={handleDownloadSVG}>
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  SVG (Vector)
                </Button>
              </div>
            </Card>

            {/* Stable URL & Info Card */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Stable QR Destination URL</CardTitle>
                  <CardDescription>
                    This permanent URL routes directly to your feedback form.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      readOnly
                      value={qrDetails.destination_url}
                      className="flex-1 h-10 px-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 font-mono select-all focus:outline-none"
                    />
                    <Button variant="outline" size="sm" onClick={handleCopyLink}>
                      {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  </div>

                  <a
                    href={qrDetails.destination_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-xs text-emerald-700 font-medium hover:underline pt-1"
                  >
                    <span>Test destination in browser</span>
                    <ExternalLink className="w-3.5 h-3.5 ml-1" />
                  </a>
                </CardContent>
              </Card>

              <Card className="bg-emerald-50/40 border-emerald-100">
                <CardContent className="p-6 space-y-2">
                  <div className="flex items-center space-x-2 text-emerald-800 font-semibold text-sm">
                    <QrCode className="w-4 h-4 text-emerald-600" />
                    <span>Permanent Print Guarantee</span>
                  </div>
                  <p className="text-xs text-emerald-950/80 leading-relaxed">
                    Once printed, you never need to replace or reprint this QR code. Even during plan changes or renewals, the destination URL remains constant.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}

