import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        wisag: {
          orange: '#E94E1B',
          orangeDark: '#FF7D4D',
          orangeLight: '#2A1A15',
          navy: '#F4F7FF',
          gray100: '#101A2B',
          gray200: '#172236',
          gray300: '#22314D',
          gray500: '#7F8AA3',
          gray600: '#A6B1C6',
        },
        pos: { DEFAULT: '#7BFF86', light: '#153522', dark: '#B6FFBF' },
        neg: { DEFAULT: '#FF6B7A', light: '#3D1821', dark: '#FFC1CA' },
        warn: { DEFAULT: '#FFBE5C', light: '#3A2912' },
      },
      fontFamily: {
        sans: ['Manrope', 'Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Arial', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
