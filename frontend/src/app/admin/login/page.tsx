"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { UtensilsCrossed, ArrowRight, Settings2 } from "lucide-react";
import { api, APIError, getApiBaseUrl, setCustomBackendUrl } from "@/lib/api";
import { setStoredToken } from "@/lib/auth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { ErrorAlert } from "@/components/common/ErrorAlert";

export default function AdminLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [showBackendConfig, setShowBackendConfig] = useState(false);
  const [backendUrlInput, setBackendUrlInput] = useState("");
  const [backendSuccess, setBackendSuccess] = useState("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const current = getApiBaseUrl();
      setBackendUrlInput(current.replace(/\/api\/v1\/?$/, ""));
    }
  }, []);

  const handleSaveBackendUrl = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!backendUrlInput.trim()) return;

    const target = backendUrlInput.trim().replace(/\/+$/, "");
    setCustomBackendUrl(target);
    setBackendSuccess("Testing connection...");

    try {
      const testRes = await fetch(`${target}/api/v1/health`, { method: "GET" });
      if (testRes.ok) {
        setBackendSuccess("Connected to Backend successfully! You can sign in now.");
        setError("");
      } else {
        setBackendSuccess(`Backend URL saved (Status ${testRes.status}).`);
      }
    } catch {
      setBackendSuccess("Backend URL saved. You can try signing in now.");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!username || !password) {
      setError("Please enter both username and password.");
      return;
    }

    try {
      setIsLoading(true);
      const res = await api.loginAdmin({ username: username.trim(), password });
      setStoredToken(res.access_token);
      router.push("/admin/dashboard");
    } catch (err: any) {
      if (err instanceof APIError) {
        setError(err.message);
        if (err.status === 0 || err.message.toLowerCase().includes("cannot connect")) {
          setShowBackendConfig(true);
        }
      } else {
        setError(
          "Cannot connect to the backend server. Please verify your backend API URL below."
        );
        setShowBackendConfig(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-emerald-600 text-white flex items-center justify-center mx-auto shadow-sm">
            <UtensilsCrossed className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Restaurant Admin Portal
          </h1>
          <p className="text-sm text-slate-500">
            Sign in to manage your QR code, view feedback analytics, and update settings.
          </p>
        </div>

        <Card className="border-slate-100 shadow-sm">
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>Enter your administration credentials</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <ErrorAlert message={error} onRetry={() => setError("")} />}

              {showBackendConfig && (
                <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-left text-xs space-y-2">
                  <div className="font-semibold text-amber-900 flex items-center gap-1.5">
                    <Settings2 className="w-3.5 h-3.5" />
                    <span>Backend Server Connection</span>
                  </div>
                  <p className="text-amber-800 text-[11px] leading-relaxed">
                    Enter your deployed Backend Vercel URL to connect this frontend to your API:
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      placeholder="https://your-backend.vercel.app"
                      value={backendUrlInput}
                      onChange={(e) => setBackendUrlInput(e.target.value)}
                      className="flex-1 px-2.5 py-1.5 text-xs bg-white border border-amber-300 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-amber-500"
                    />
                    <button
                      type="button"
                      onClick={() => handleSaveBackendUrl()}
                      className="px-3 py-1.5 bg-amber-800 text-white rounded-lg font-medium text-xs hover:bg-amber-900 transition-colors whitespace-nowrap"
                    >
                      Save &amp; Test
                    </button>
                  </div>
                  {backendSuccess && (
                    <p className="text-emerald-700 font-medium text-[11px] mt-1">{backendSuccess}</p>
                  )}
                </div>
              )}

              <Input
                label="Administrator Username"
                type="text"
                placeholder="aslam or admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />

              <Input
                label="Password"
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />

              <div className="text-[11px] text-slate-400 text-center py-0.5">
                Username: <strong className="text-slate-600">aslam</strong> or <strong className="text-slate-600">admin</strong> &bull; Password: <strong className="text-slate-600">aslam0077</strong>
              </div>

              <Button
                type="submit"
                size="lg"
                className="w-full mt-2"
                isLoading={isLoading}
              >
                <span>Sign In to Dashboard</span>
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>

              <div className="text-center pt-1">
                <button
                  type="button"
                  onClick={() => setShowBackendConfig(!showBackendConfig)}
                  className="text-[11px] text-slate-400 hover:text-slate-600 underline"
                >
                  {showBackendConfig ? "Hide backend URL settings" : "Configure Backend API URL"}
                </button>
              </div>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-slate-400">
          Independent Installation &bull; Secure Encrypted Session
        </p>
      </div>
    </div>
  );
}
