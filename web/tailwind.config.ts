import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        wisag: {
          orange: '#E94E1B',
          orangeDark: '#C63D0F',
          orangeLight: '#FDE6DC',
          navy: '#1D1D1B',
          gray100: '#F5F5F5',
          gray200: '#EDEDED',
          gray300: '#E5E5E5',
          gray500: '#9E9E9E',
          gray600: '#6B6B6B',
        },
        pos: { DEFAULT: '#2E7D32', light: '#C8E6C9', dark: '#1B5E20' },
        neg: { DEFAULT: '#C62828', light: '#FFCDD2', dark: '#B71C1C' },
        warn: { DEFAULT: '#F57C00', light: '#FFE0B2' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
