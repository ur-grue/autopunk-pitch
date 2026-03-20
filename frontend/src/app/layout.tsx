import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-body",
  weight: "100 900",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-display",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Autopunk Localize",
  description: "AI-powered media localization at indie pricing",
};

const hasClerk = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

function AuthWrapper({ children }: { children: React.ReactNode }) {
  if (!hasClerk) return <>{children}</>;

  // Dynamic import to avoid build errors when Clerk key is missing
  const { ClerkProvider } = require("@clerk/nextjs");

  const clerkAppearance = {
    variables: {
      colorPrimary: "#c3c0ff",
      colorBackground: "#201e2e",
      colorText: "#e5dff7",
      colorTextSecondary: "#c7c4d8",
      colorInputBackground: "transparent",
      colorInputText: "#e5dff7",
      borderRadius: "0.125rem",
    },
  };

  return <ClerkProvider appearance={clerkAppearance}>{children}</ClerkProvider>;
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthWrapper>
      <html lang="en">
        <body
          className={`${geistSans.variable} ${geistMono.variable} font-body antialiased bg-surface text-on-surface min-h-screen`}
        >
          {children}
        </body>
      </html>
    </AuthWrapper>
  );
}
