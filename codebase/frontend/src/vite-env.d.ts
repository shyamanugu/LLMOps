/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the LLMOps platform API (e.g. http://localhost:8000/api/v1). */
  readonly VITE_API_BASE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
