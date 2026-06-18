/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#020617', // slate-950
        foreground: '#f8fafc', // slate-50
        panel: 'rgba(15, 23, 42, 0.6)', // slate-900 with opacity
        glass: 'rgba(255, 255, 255, 0.03)',
        line: 'rgba(255, 255, 255, 0.1)',
        primary: '#3b82f6', // blue-500
        'primary-glow': 'rgba(59, 130, 246, 0.5)',
        accent: '#8b5cf6', // violet-500
        'accent-glow': 'rgba(139, 92, 246, 0.5)',
        // Dashboard component color aliases
        cyan:   '#22d3ee',
        green:  '#4ade80',
        amber:  '#fbbf24',
        violet: '#a78bfa',
        rose:   '#fb7185',
        'hero-sub': 'rgba(248, 250, 252, 0.7)',
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["Fira Code", "JetBrains Mono", "monospace"],
      },
      animation: {
        'blob': 'blob 7s infinite',
        'fade-in-up': 'fadeInUp 0.8s ease-out forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'marquee': 'marquee 20s linear infinite',
      },
      keyframes: {
        blob: {
          '0%': { transform: 'translate(0px, 0px) scale(1)' },
          '33%': { transform: 'translate(30px, -50px) scale(1.1)' },
          '66%': { transform: 'translate(-20px, 20px) scale(0.9)' },
          '100%': { transform: 'translate(0px, 0px) scale(1)' },
        },
        fadeInUp: {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        marquee: {
          '0%':   { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      }
    },
  },
  plugins: [],
}
