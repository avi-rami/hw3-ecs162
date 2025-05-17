// frontend/vite.config.ts
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [svelte()],
  server: mode === 'development' ? {
    proxy: {
      // proxy all /api/* calls to your Flask container
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            console.log('Proxying request:', req.url)
          })
        }
      },
      // OAuth endpoints also go to Flask, and we rewrite the cookie domain:
      '/login': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
        // Rewrite Set-Cookie domain so browser will accept it for localhost
        cookieDomainRewrite: 'localhost'
      },
      '/authorize': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
        cookieDomainRewrite: 'localhost'
      },
      '/logout': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
        cookieDomainRewrite: 'localhost'
      },
    },
  } : undefined,
}))


// // frontend/vite.config.ts
// import { defineConfig } from 'vite'
// import { svelte } from '@sveltejs/vite-plugin-svelte'

// // https://vite.dev/config/
// export default defineConfig(({ mode }) => ({
//   plugins: [svelte()],
//   server: mode === 'development' ? {
//     proxy: {
//       // proxy all /api/* calls to your Flask container
//       '/api': {
//         target: 'http://backend:8000',
//         changeOrigin: true,
//         secure: false,
//         configure: (proxy, options) => {
//           proxy.on('proxyReq', (proxyReq, req, res) => {
//             console.log('Proxying request:', req.url)
//           })
//         }
//       },
//       // OAuth endpoints also go to Flask
//       '/login': {
//         target: 'http://backend:8000',
//         changeOrigin: true,
//         secure: false,
//       },
//       '/authorize': {
//         target: 'http://backend:8000',
//         changeOrigin: true,
//         secure: false,
//       },
//       '/logout': {
//         target: 'http://backend:8000',
//         changeOrigin: true,
//         secure: false,
//       },
//     },
//   } : undefined,
// }))

// OLD CODE BELOW

// import { defineConfig } from 'vite'
// import { svelte } from '@sveltejs/vite-plugin-svelte'

// // https://vite.dev/config/
// export default defineConfig(({ mode }) => ({
//   plugins: [svelte()],
//   server: mode === 'development' ? {
//     proxy: {
//       '/api': {
//         target: 'http://localhost:8000',
//         changeOrigin: true,
//         secure: false,
//         // rewrite the cookie’s domain so your browser accepts it on localhost
//         cookieDomainRewrite: 'localhost',
//         configure: (proxy, options) => {
//           proxy.on('proxyReq', (proxyReq, req, res) => {
//             console.log('Proxying request:', req.url)
//           })
//         }
//       },
//       // ─── OAuth routes ─────────────────────────────────────────────────────────
//       '/login': {
//         target: 'http://localhost:8000',
//         changeOrigin: true,
//         secure: false,
//         cookieDomainRewrite: 'localhost',
//       },
//       '/authorize': {
//         target: 'http://localhost:8000',
//         changeOrigin: true,
//         secure: false,
//         cookieDomainRewrite: 'localhost',
//       },
//       '/logout': {
//         target: 'http://localhost:8000',
//         changeOrigin: true,
//         secure: false,
//         cookieDomainRewrite: 'localhost',
//       },
//       // ─────────────────────────────────────────────────────────────────────────
//     },
//   } : undefined,
// }))



// import { defineConfig } from 'vite'
// import { svelte } from '@sveltejs/vite-plugin-svelte'

// // https://vite.dev/config/
// export default defineConfig(({ mode }) => ({
//   plugins: [svelte()],
//   server: mode === 'development' ? {
//     proxy: {
//       '/api': {
//         target: 'http://backend:8000',
//         changeOrigin: true,
//         secure: false,
//         configure: (proxy, options) => {
//           proxy.on('proxyReq', (proxyReq, req, res) => {
//             console.log('Proxying request:', req.url)
//           })
//         }
//       },
//     },
//   } : undefined,
// }))