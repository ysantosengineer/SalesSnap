import type { Metadata } from "next";

import { AppNavigation } from "@/components/app-navigation";
import { AuthProvider } from "@/components/auth-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "SalesSnap",
  description: "Multi-tenant sales intelligence with analytics, machine learning, and AI.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <AppNavigation />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
