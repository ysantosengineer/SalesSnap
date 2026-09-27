"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  type AuthenticatedUser,
  login as loginRequest,
  logout as logoutRequest,
  refreshSession,
  register as registerRequest,
} from "@/lib/auth-api";

type AuthContextValue = {
  user: AuthenticatedUser | null;
  accessToken: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (companyName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    refreshSession()
      .then((session) => {
        setUser(session.user);
        setAccessToken(session.access_token);
      })
      .catch(() => {
        setUser(null);
        setAccessToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isLoading,
      login: async (email, password) => {
        const session = await loginRequest(email, password);
        setUser(session.user);
        setAccessToken(session.access_token);
      },
      register: async (companyName, email, password) => {
        const session = await registerRequest(companyName, email, password);
        setUser(session.user);
        setAccessToken(session.access_token);
      },
      logout: async () => {
        await logoutRequest();
        setUser(null);
        setAccessToken(null);
      },
    }),
    [accessToken, isLoading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
