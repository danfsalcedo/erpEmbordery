import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'ERP Bordados',
        short_name: 'Bordados',
        theme_color: '#0f172a',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        icons: [],
      },
    }),
  ],
  server: {
    host: true,
    port: 5173,
    // Polling necesario para que el HMR detecte cambios en bind mounts de Windows/Docker
    watch: { usePolling: true },
  },
})
