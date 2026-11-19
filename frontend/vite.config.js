import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // собранные файлы раздаёт Django по адресу /static/
  base: command === "build" ? "/static/" : "/",
  server: {
    port: 5173,
    // при разработке запросы к API уходят на локальный сервер Django
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
}));
