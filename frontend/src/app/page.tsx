"use client";

import Link from "next/link";

const hasClerk = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

function useAuthSafe() {
  if (!hasClerk) return { isSignedIn: false, isLoaded: true };
  try {
    const { useAuth } = require("@clerk/nextjs");
    return useAuth();
  } catch {
    return { isSignedIn: false, isLoaded: true };
  }
}

export default function Home() {
  const { isSignedIn, isLoaded } = useAuthSafe();

  return (
    <main className="relative z-10 flex min-h-screen flex-col items-center justify-center p-8">
      {/* Decorative Elements */}
      <div className="fixed top-1/3 left-1/4 w-[300px] h-[300px] bg-primary/8 blur-[100px] rounded-full pointer-events-none" />
      <div className="fixed bottom-1/4 right-1/3 w-[200px] h-[200px] bg-tertiary/5 blur-[80px] rounded-full pointer-events-none" />

      <div className="max-w-3xl text-center">
        {/* Production Node Label */}
        <div className="font-display text-tertiary text-xs uppercase tracking-[0.2em] mb-6">
          AI-Powered Localization Engine
        </div>

        <h1 className="font-display text-5xl md:text-7xl font-bold tracking-tighter text-on-surface mb-2 leading-[0.95]">
          BROADCAST QUALITY.
          <br />
          <span className="text-primary">INDIE PRICING.</span>
        </h1>

        <p className="text-on-surface-variant text-lg md:text-xl mt-6 mb-10 max-w-xl mx-auto leading-relaxed">
          Upload a video, get subtitles in multiple languages.
          AI transcription, translation, and cultural adaptation
          in a single pipeline.
        </p>

        {isLoaded && !isSignedIn && (
          <>
            <div className="flex gap-4 justify-center">
              <Link
                href={hasClerk ? "/sign-in" : "/dashboard"}
                className="btn-gradient font-display px-8 py-4 text-xs font-bold uppercase tracking-[0.2em] rounded hover:shadow-glow active:scale-[0.98] transition-all duration-200"
              >
                Initialize Session
              </Link>
              <Link
                href={hasClerk ? "/sign-up" : "/dashboard"}
                className="ghost-border text-primary px-8 py-4 font-display text-xs font-bold uppercase tracking-[0.2em] rounded hover:bg-surface-container-high transition-all duration-200"
              >
                Create Account
              </Link>
            </div>
            <p className="mt-8 label-uppercase text-outline tracking-widest">
              Free tier: 10 minutes/month &middot; 3 languages &middot; SRT export
            </p>
          </>
        )}

        {isLoaded && isSignedIn && (
          <Link
            href="/dashboard"
            className="btn-gradient font-display px-10 py-4 text-xs font-bold uppercase tracking-[0.2em] rounded hover:shadow-glow active:scale-[0.98] transition-all duration-200"
          >
            Enter Dashboard
          </Link>
        )}
      </div>

      {/* Footer Meta */}
      <div className="fixed bottom-0 left-0 w-full z-20 pointer-events-none">
        <div className="flex justify-between items-center px-8 py-6 max-w-7xl mx-auto">
          <span className="font-display text-[9px] text-outline-variant uppercase tracking-widest pointer-events-auto">
            &copy; 2024 Autopunk Localize. Cinematic Intelligence.
          </span>
          <span className="font-display text-[9px] text-outline-variant uppercase tracking-widest pointer-events-auto">
            v1.0.0-alpha
          </span>
        </div>
      </div>
    </main>
  );
}
