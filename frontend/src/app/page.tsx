import { Utensils, QrCode, ShieldCheck, BarChart3, ArrowRight } from "lucide-react";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col justify-between p-6 sm:p-12 max-w-4xl mx-auto">
      <div className="space-y-8 my-auto py-12">
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Independent Restaurant Installation</span>
        </div>

        <div className="space-y-4">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 leading-tight">
            Restaurant QR Feedback &amp; Google Review Assistance
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl leading-relaxed">
            A private, independent customer feedback and review assistance platform designed specifically for fine dining and hospitality establishments.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
          <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs space-y-2">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <QrCode className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-900 text-sm">Dynamic QR System</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Permanent QR code that never needs reprinting. Configured directly for this venue.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs space-y-2">
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Utensils className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-900 text-sm">Direct Customer Feedback</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Mobile-optimized feedback on food, service, and ambience with optional Google review assistance.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs space-y-2">
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-900 text-sm">Simple Dashboard</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Strictly focused on the 4 essential metrics: scans, feedback, review clicks, and monthly activity.
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 pt-6">
          <a
            href="/r/paradise-restaurant"
            className="inline-flex items-center justify-center h-12 px-6 rounded-xl bg-emerald-600 text-white font-medium hover:bg-emerald-700 transition-colors shadow-sm"
          >
            <span>Preview Customer Feedback Flow</span>
            <ArrowRight className="w-4 h-4 ml-2" />
          </a>

          <a
            href="/admin/login"
            className="inline-flex items-center justify-center h-12 px-6 rounded-xl border border-slate-200 bg-white text-slate-700 font-medium hover:bg-slate-50 transition-colors"
          >
            Restaurant Admin Login
          </a>
        </div>
      </div>

      <footer className="text-xs text-slate-400 text-center py-6 border-t border-slate-100">
        Single-Tenant Commercial Installation &bull; Zero Shared Data &bull; Fully Independent Deployment
      </footer>
    </main>
  );
}

