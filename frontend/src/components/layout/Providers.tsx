"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 60_000, retry: 1 } }
  }));
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "hsl(222 47% 9%)",
            color: "hsl(210 40% 98%)",
            border: "1px solid hsl(222 47% 14%)",
            borderRadius: "12px",
            fontSize: "13px",
          },
        }}
      />
    </QueryClientProvider>
  );
}
