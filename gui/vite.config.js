import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  base: process.env.NODE_ENV === 'production' ? '/midi-obs-controller/' : '/',
  server: {
    host: true,  // expose on network + show hostname in the startup banner
  },
})
