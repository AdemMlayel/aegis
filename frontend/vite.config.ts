import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, frontendRoot, "");
  return {
    root: frontendRoot,
    plugins: [react()],
    build: {
      outDir: "dist"
    },
    server: {
      host: env.VITE_DEV_HOST ?? "127.0.0.1",
      port: Number(env.VITE_DEV_PORT ?? 5173),
      // Allow extra hostnames (e.g. a temporary tunnel domain) for remote
      // preview. Comma-separated; defaults to localhost-only.
      allowedHosts: env.VITE_ALLOWED_HOSTS
        ? env.VITE_ALLOWED_HOSTS.split(",").map((h) => h.trim()).filter(Boolean)
        : undefined,
      proxy: {
        "/api": {
          target: env.VITE_API_PROXY_TARGET ?? "http://127.0.0.1:8000",
          changeOrigin: true
        }
      }
    }
  };
});
