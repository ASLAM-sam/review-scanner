"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, Mail, UtensilsCrossed, ArrowRight } from "lucide-react";
import { api, APIError } from "@/lib/api";
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
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Unable to authenticate. Please verify your credentials.");
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

              <Input
                label="Administrator Username"
                type="text"
                placeholder="aslam"
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
                required
              />

              <Button
                type="submit"
                size="lg"
                className="w-full mt-2"
                isLoading={isLoading}
              >
                <span>Sign In to Dashboard</span>
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
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

