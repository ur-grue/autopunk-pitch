import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#131122",
          container: {
            DEFAULT: "#1a1830",
            low: "#15132a",
            high: "#211f3a",
          },
          bright: "#2a2845",
        },
        "on-surface": {
          DEFAULT: "#e5dff7",
          variant: "#918fa1",
        },
        primary: {
          DEFAULT: "#c3c0ff",
          container: {
            DEFAULT: "rgba(79, 70, 229, 0.25)",
          },
        },
        tertiary: {
          DEFAULT: "#ffb95f",
          container: {
            DEFAULT: "rgba(255, 185, 95, 0.2)",
          },
        },
        error: {
          DEFAULT: "#f87171",
        },
        outline: {
          DEFAULT: "#464555",
          variant: {
            DEFAULT: "rgba(70, 69, 85, 0.5)",
          },
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "monospace"],
        body: ["var(--font-body)", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(195, 192, 255, 0.15)",
        "glow-sm": "0 0 12px rgba(195, 192, 255, 0.1)",
      },
    },
  },
  plugins: [],
};

export default config;
