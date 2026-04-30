import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Security Copilot",
  description: "AI-powered cybersecurity risk analyst",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}