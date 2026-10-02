import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-navigation";
import { AuthProvider } from "@/components/auth-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "SalesSnap",
  description: "Multi-tenant sales intelligence with analytics, machine learning, and AI.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
