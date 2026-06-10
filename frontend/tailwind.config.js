/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        'hero-sub': 'hsl(var(--hero-sub))',
        panel: 'rgba(250, 248, 245, 0.95)',
        glass: 'rgba(0, 0, 0, 0.05)',
        line: 'rgba(0, 0, 0, 0.15)',
        midground: '#1c1917', // Off-black
        cream: '#faf8f5',     // Vintage cream
        'accent-red': '#ff2702', // Nous orange-red
        cyan: '#06b6d4',
        green: '#10b981',
      },
      fontFamily: {
        display: ["VT323", "monospace"],
        body: ["Courier Prime", "monospace"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
        sharetech: ["Share Tech Mono", "monospace"],
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        marquee: 'marquee 25s linear infinite',
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(-50%)' },
        }
      }
    },
  },
  plugins: [],
}
