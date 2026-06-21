"use client";
import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    try {
      await api.post("/api/auth/forgot-password", { email });
      setSent(true);
    } catch {
      toast.error("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
            <span className="text-black font-bold text-sm">A</span>
          </div>
          <span className="text-white font-semibold text-xl">ALLOCENSUS</span>
        </div>

        <div className="bg-[#111118] border border-white/10 rounded-xl p-8">
          {sent ? (
            <div className="text-center">
              <div className="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h1 className="text-white text-xl font-semibold mb-2">Check your email</h1>
              <p className="text-gray-400 text-sm mb-6">If an account exists for <strong className="text-white">{email}</strong>, a reset link has been sent.</p>
              <Link href="/login" className="text-emerald-400 hover:text-emerald-300 text-sm transition-colors">
                Back to login
              </Link>
            </div>
          ) : (
            <>
              <h1 className="text-white text-xl font-semibold mb-1">Reset your password</h1>
              <p className="text-gray-400 text-sm mb-6">Enter your work email and we&apos;ll send a reset link.</p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5">Work email</label>
                  <input
                    type="email"
                    required
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
                    placeholder="you@firm.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-semibold py-2.5 rounded-lg transition-colors"
                >
                  {loading ? "Sending…" : "Send reset link"}
                </button>
              </form>
              <p className="text-center text-sm text-gray-500 mt-5">
                Remembered it?{" "}
                <Link href="/login" className="text-emerald-400 hover:text-emerald-300 transition-colors">Sign in</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
