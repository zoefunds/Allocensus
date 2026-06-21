"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { authAPI } from "@/lib/api";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setMessage("No verification token found.");
      return;
    }
    authAPI.verifyEmail(token)
      .then(() => {
        setStatus("success");
        setMessage("Your email has been verified. You can now log in.");
        setTimeout(() => router.push("/login"), 3000);
      })
      .catch(() => {
        setStatus("error");
        setMessage("This verification link is invalid or has expired.");
      });
  }, [searchParams, router]);

  return (
    <div className="bg-[#111118] border border-white/10 rounded-xl p-8">
      {status === "loading" && (
        <>
          <div className="w-12 h-12 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <h1 className="text-white text-xl font-semibold">Verifying your email…</h1>
        </>
      )}
      {status === "success" && (
        <>
          <div className="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-white text-xl font-semibold mb-2">Email Verified</h1>
          <p className="text-gray-400 text-sm">{message}</p>
          <p className="text-gray-500 text-xs mt-3">Redirecting to login…</p>
        </>
      )}
      {status === "error" && (
        <>
          <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-white text-xl font-semibold mb-2">Verification Failed</h1>
          <p className="text-gray-400 text-sm mb-6">{message}</p>
          <a href="/login" className="inline-block bg-emerald-500 text-black font-semibold px-6 py-2 rounded-lg hover:bg-emerald-400 transition-colors">
            Go to Login
          </a>
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-md text-center">
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
            <span className="text-black font-bold text-sm">A</span>
          </div>
          <span className="text-white font-semibold text-xl">ALLOCENSUS</span>
        </div>
        <Suspense fallback={
          <div className="bg-[#111118] border border-white/10 rounded-xl p-8">
            <div className="w-12 h-12 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        }>
          <VerifyEmailContent />
        </Suspense>
      </div>
    </div>
  );
}
