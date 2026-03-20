"use client";

import Link from "next/link";

export function Navbar() {
  return (
    <nav className="glass ghost-border-b sticky top-0 z-30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link
              href="/"
              className="font-display text-sm font-bold tracking-[0.15em] text-primary uppercase"
            >
              Autopunk
            </Link>
            <Link
              href="/dashboard"
              className="font-display text-xs uppercase tracking-wider text-on-surface-variant hover:text-on-surface transition-colors"
            >
              Projects
            </Link>
          </div>
          <div className="flex items-center gap-4">
            <span className="font-display text-[10px] text-outline uppercase tracking-widest">
              v1.0.0-alpha
            </span>
            <div className="h-7 w-7 rounded-full bg-primary/20 border border-primary/30" />
          </div>
        </div>
      </div>
    </nav>
  );
}
