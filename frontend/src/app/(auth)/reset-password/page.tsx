"use client";
import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import Link from "next/link";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) return toast.error("Passwords don't match");
    if (password.length < 8) return toast.error("Password must be at least 8 characters");
    setLoading(true);
    try {
      await api.post("/api/auth/reset-password", { token, new_password: password });
      toast.success("Password reset! Redirecting to login…");
      setTimeout(() => router.push("/login"), 2000);
    } catch {
      toast.error("Invalid or expired reset link. Please request a new one.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="text-center">
        <p className="text-gray-400 mb-4">No reset token found.</p>
        <Link href="/forgot-password" className="text-emerald-400 hover:text-emerald-300 text-sm">Request a new link</Link>
      </div>
    );
  }

  return (
    <>
      <h1 className="text-white text-xl font-semibold mb-1">Set new password</h1>
      <p className="text-gray-400 text-sm mb-6">Choose a strong password for your account.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">New password</label>
          <input
            type="password"
            required
            minLength={8}
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
            placeholder="At least 8 characters"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">Confirm password</label>
          <input
            type="password"
            required
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
            placeholder="Repeat your new password"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-semibold py-2.5 rounded-lg transition-colors"
        >
          {loading ? "Resetting…" : "Reset password"}
        </button>
      </form>
      <p className="text-center text-sm text-gray-500 mt-5">
        <Link href="/login" className="text-emerald-400 hover:text-emerald-300 transition-colors">Back to login</Link>
      </p>
    </>
  );
}

export default function ResetPasswordPage() {
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
          <Suspense fallback={<div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />}>
            <ResetPasswordForm />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
