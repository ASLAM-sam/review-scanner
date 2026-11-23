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
        brand: {
          50: "var(--brand-50, #f0fdf4)",
          100: "var(--brand-100, #dcfce7)",
          200: "var(--brand-200, #bbf7d0)",
          500: "var(--brand-500, #16a34a)",
          600: "var(--brand-600, #15803d)",
          700: "var(--brand-700, #166534)",
          900: "var(--brand-900, #14532d)",
        },
      },
    },
  },
  plugins: [],
};

export default config;

