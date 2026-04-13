import { defineConfig } from 'vite'
import { loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  //VITE_USE_LEADER_API：true--使用wxj统一后端的地址，否则使用自己pc上的后端地址。
  //VITE_API_TARGET_LOCAL：本地后端地址，默认http://127.0.0.1:8000。
  //VITE_API_TARGET_LEADER：wxj后端地址，默认http://127.0.0.1:8000（后面建库后再改）。
  //apiTarget--实际要代理的目标地址。
  const env = loadEnv(mode, process.cwd(), '')
  const useLeaderApi = (env.VITE_USE_LEADER_API || 'false').toLowerCase() === 'true'
  const localTarget = env.VITE_API_TARGET_LOCAL || 'http://127.0.0.1:8000'
  const leaderTarget = env.VITE_API_TARGET_LEADER || 'http://127.0.0.1:8000'
  const apiTarget = useLeaderApi ? leaderTarget : localTarget

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: apiTarget, 
          changeOrigin: true
        }
      }
    }
  }
})
