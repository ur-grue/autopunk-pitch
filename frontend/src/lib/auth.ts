"use client";

const hasClerk = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

type AuthResult = {
  getToken: () => Promise<string | null>;
  isSignedIn: boolean;
  isLoaded: boolean;
};

export function useAuthSafe(): AuthResult {
  if (!hasClerk) {
    return {
      getToken: async () => null,
      isSignedIn: false,
      isLoaded: true,
    };
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { useAuth } = require("@clerk/nextjs");
    return useAuth();
  } catch {
    return {
      getToken: async () => null,
      isSignedIn: false,
      isLoaded: true,
    };
  }
}
