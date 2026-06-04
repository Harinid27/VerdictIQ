/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: "#0B0F19",
          dark: "#111827",
          blue: "#4F8CFF",
          purple: "#7B61FF",
          glow: "rgba(79, 140, 255, 0.15)",
          border: "rgba(255, 255, 255, 0.08)",
          textMuted: "#9CA3AF",
        }
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        display: ["Space Grotesk", "sans-serif"],
      },
      boxShadow: {
        'glass-glow': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'premium-card': '0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
        'button-glow': '0 0 20px 2px rgba(79, 140, 255, 0.3), 0 0 40px 4px rgba(123, 97, 255, 0.2)',
      },
      animation: {
        'shine-sweep': 'shine 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        shine: {
          '0%': { left: '-100%' },
          '100%': { left: '200%' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      }
    },
  },
  plugins: [],
}
