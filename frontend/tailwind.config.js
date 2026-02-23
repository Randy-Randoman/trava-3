/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors for TRAVA branding
        'retro-cream': '#FDFBF7',
        'trava-teal': '#20C997',
        'trava-teal-light': '#E6FAF5',
        'adventure-orange': '#FF8C42',
        'adventure-orange-light': '#FFF0E0',
        'trava-black': '#1A1A1B',
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        brand: ['Space Grotesk', 'sans-serif'],
      },
      boxShadow: {
        'brutal': '8px 8px 0px #1A1A1B',
        'brutal-sm': '4px 4px 0px #1A1A1B',
      },
    },
  },
  plugins: [],
}
