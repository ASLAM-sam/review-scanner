"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Save, Check, UtensilsCrossed } from "lucide-react";
import { api, APIError } from "@/lib/api";
import { isUserAuthenticated } from "@/lib/auth";
import { Navbar } from "@/components/common/Navbar";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorAlert } from "@/components/common/ErrorAlert";
import type { RestaurantAdminInfo, RestaurantUpdatePayload } from "@/types";

export default function AdminSettingsPage() {
  const router = useRouter();
  const [restaurant, setRestaurant] = useState<RestaurantAdminInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState("");

  // Form states
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [googleReviewUrl, setGoogleReviewUrl] = useState("");
  const [primaryColor, setPrimaryColor] = useState("#16a34a");
  const [contactPhone, setContactPhone] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [address, setAddress] = useState("");

  useEffect(() => {
    async function loadSettings() {
      try {
        setIsLoading(true);
        if (!isUserAuthenticated()) {
          router.push("/admin/login");
          return;
        }

        const data = await api.getAdminRestaurant();
        setRestaurant(data);
        setName(data.name || "");
        setDescription(data.description || "");
        setGoogleReviewUrl(data.google_review_url || "");
        setPrimaryColor(data.primary_color || "#16a34a");
        setContactPhone(data.contact_phone || "");
        setContactEmail(data.contact_email || "");
        setAddress(data.address || "");
      } catch (err) {
        if (err instanceof APIError && err.status === 401) {
          router.push("/admin/login");
        } else {
          setError("Failed to load restaurant settings.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadSettings();
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(false);
    setError("");

    try {
      setIsSaving(true);
      const payload: RestaurantUpdatePayload = {
        name,
        description,
        google_review_url: googleReviewUrl,
        primary_color: primaryColor,
        contact_phone: contactPhone,
        contact_email: contactEmail,
        address,
      };

      const updated = await api.updateAdminRestaurant(payload);
      setRestaurant(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Failed to update settings. Please try again.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar restaurantName={restaurant?.name} />

      <main className="flex-1 max-w-3xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Restaurant Configuration
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Customize branding, Google Review destination, and venue details without altering source code.
          </p>
        </div>

        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner label="Loading settings..." />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && <ErrorAlert message={error} onRetry={() => setError("")} />}

            {savedSuccess && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 flex items-center space-x-2 text-sm font-medium">
                <Check className="w-4 h-4 text-emerald-600" />
                <span>Restaurant configuration updated successfully!</span>
              </div>
            )}

            {/* Branding Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Branding &amp; Identity</CardTitle>
                <CardDescription>
                  Customer-facing restaurant identity shown on the feedback page.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  label="Restaurant Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />

                <Textarea
                  label="Restaurant Tagline / Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Authentic Artisan Italian Cuisine"
                />

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Primary Brand Color
                  </label>
                  <div className="flex items-center space-x-3">
                    <input
                      type="color"
                      value={primaryColor}
                      onChange={(e) => setPrimaryColor(e.target.value)}
                      className="w-10 h-10 rounded-xl cursor-pointer border border-slate-200 p-0.5 bg-white"
                    />
                    <input
                      type="text"
                      value={primaryColor}
                      onChange={(e) => setPrimaryColor(e.target.value)}
                      className="w-32 h-10 px-3 bg-white border border-slate-200 rounded-xl text-sm font-mono text-slate-700 uppercase"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Google Review URL Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Google Review Link</CardTitle>
                <CardDescription>
                  The official Google Review submission link presented to your guests.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Input
                  label="Google Review URL"
                  value={googleReviewUrl}
                  onChange={(e) => setGoogleReviewUrl(e.target.value)}
                  placeholder="https://g.page/r/your-google-place-id/review"
                  helperText="Obtained from your Google Business Profile manager ('Ask for reviews' button)."
                  required
                />
              </CardContent>
            </Card>

            {/* Contact Information Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Contact Information</CardTitle>
                <CardDescription>
                  Optional venue details shown in communication headers.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Phone Number"
                    value={contactPhone}
                    onChange={(e) => setContactPhone(e.target.value)}
                    placeholder="+1 (555) 000-0000"
                  />
                  <Input
                    label="Contact Email"
                    type="email"
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    placeholder="manager@restaurant.com"
                  />
                </div>

                <Input
                  label="Physical Address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="123 Gourmet Street, City, State"
                />
              </CardContent>
            </Card>

            <div className="flex justify-end pt-2">
              <Button type="submit" size="lg" isLoading={isSaving} className="w-full sm:w-auto">
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}

