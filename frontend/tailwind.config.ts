import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        surface: {
          950: '#070b12',
          900: '#0b111c',
          850: '#101826',
          800: '#142033',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
