/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        // Semantic & Brand Colors from Design System
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb', // Brand Main Action
          700: '#1d4ed8',
        },
        slate: {
          50: '#f8fafc', // Background
          200: '#e2e8f0', // Borders
          500: '#64748b', // Secondary Text
          900: '#0f172a', // Primary Text
        },
        success: '#059669', // Emerald
        error: '#dc2626',   // Red
        warning: '#d97706', // Amber
      },
      boxShadow: {
        'card': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [],
}
