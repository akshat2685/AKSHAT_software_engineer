/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#03050b',
        'bg-2': '#07111c',
        panel: 'rgba(8, 13, 25, 0.68)',
        glass: 'rgba(255, 255, 255, 0.075)',
        line: 'rgba(255, 255, 255, 0.14)',
        cyan: '#38d5ff',
        green: '#4cf2a1',
        amber: '#ffd166',
        danger: '#ff6b7d',
        violet: '#a78bfa',
      },
      fontFamily: {
        display: ["Bahnschrift", "Segoe UI Variable Display", "sans-serif"],
        body: ["Aptos", "Segoe UI Variable Text", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
