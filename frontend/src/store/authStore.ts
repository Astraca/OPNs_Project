import { create } from "zustand";

import type { AuthUser } from "../types/auth";


type AuthState = {
  token: string | null;
  user: AuthUser | null;
  setSession: (token: string, user: AuthUser) => void;
  clearSession: () => void;
};

const storedToken = localStorage.getItem("opns_token");
const storedUser = localStorage.getItem("opns_user");

export const useAuthStore = create<AuthState>((set) => ({
  token: storedToken,
  user: storedUser ? (JSON.parse(storedUser) as AuthUser) : null,
  setSession: (token, user) => {
    localStorage.setItem("opns_token", token);
    localStorage.setItem("opns_user", JSON.stringify(user));
    set({ token, user });
  },
  clearSession: () => {
    localStorage.removeItem("opns_token");
    localStorage.removeItem("opns_user");
    set({ token: null, user: null });
  },
}));
