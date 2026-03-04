import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    tailwindcss(),
    sveltekit()
  ],
  server: {
    port: 5199,
    proxy: {
      '/api': 'http://localhost:8000',
      '/auth': 'http://localhost:8000'
    }
  }
});
