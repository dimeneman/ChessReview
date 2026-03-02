/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        'chess-dark-bg': '#302e2b',
        'chess-panel': '#262421',
        'chess-panel-light': '#373531',
        'chess-border': '#3c3a37',
        'chess-border-light': '#4a4845',
        'chess-green': '#81b64c',
        'chess-green-hover': '#709e43',
        'chess-green-active': '#5e8837',
      }
    },
  },
  plugins: [],
};
