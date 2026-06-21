import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  walletAddress: string | null;
  setAuth: (user: User, access: string, refresh: string, wallet?: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      walletAddress: null,
      isAuthenticated: false,
      setAuth: (user, access, refresh, wallet) => {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        set({ user, accessToken: access, refreshToken: refresh, walletAddress: wallet ?? null, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, accessToken: null, refreshToken: null, walletAddress: null, isAuthenticated: false });
      },
    }),
    { name: "allocensus-auth", partialize: (s) => ({ user: s.user, accessToken: s.accessToken, refreshToken: s.refreshToken, walletAddress: s.walletAddress, isAuthenticated: s.isAuthenticated }) }
  )
);
