/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: {
          DEFAULT: '#FFFEF7',
          warm: '#FFF9F0',
        },
        rose: {
          dusty: '#D4A5A5',
          dark: '#C49494',
          light: '#E5C4C4',
        },
        sage: {
          DEFAULT: '#9CAF88',
          dark: '#7A9A6D',
          light: '#B5C9A5',
        },
        charcoal: {
          DEFAULT: '#2C3E50',
          light: '#3A4E62',
        },
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"Lato"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
      },
      letterSpacing: {
        widest: '0.3em',
        wider: '0.2em',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
