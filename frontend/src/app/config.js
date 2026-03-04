/**
 * Frontend config from environment.
 * Next.js exposes only env vars prefixed with NEXT_PUBLIC_ to the browser.
 */
const getEnv = (key, fallback) =>
  (typeof process !== 'undefined' && process.env[key]) || fallback

export const API_BASE_URL =
  getEnv('NEXT_PUBLIC_API_URL', 'http://localhost:8000').replace(/\/$/, '')

export const APP_ORIGIN =
  getEnv('NEXT_PUBLIC_APP_ORIGIN', 'http://localhost:3000').replace(/\/$/, '')
