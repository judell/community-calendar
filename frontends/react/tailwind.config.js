import flowbite from 'flowbite-react/tailwind'

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'selector',
  content: [
    './index.html',
    './src/**/*.{js,jsx}',
    flowbite.content(),
  ],
  theme: {
    extend: {},
  },
  corePlugins: {
    preflight: false,
  },
  plugins: [
    flowbite.plugin(),
  ],
}
