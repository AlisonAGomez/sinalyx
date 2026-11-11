/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_SINALYX_NEW_LOGIN_LANDING?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
