import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0f0f1a",
        card: "#1a1b2e",
        neonCyan: "#00f9ff",
        neonPurple: "#c300ff",
        textMain: "#e0e0ff",
        textMuted: "#a0a0cc",
      },
      borderRadius: {
        '3xl': "1.5rem",
        '4xl': "2rem",
      },
      boxShadow: {
        neon: "0 0 25px rgba(195, 0, 255, 0.25)",
        neonCyan: "0 0 20px rgba(0, 249, 255, 0.5)",
      },
    },
  },
  plugins: [],
};
export default config;