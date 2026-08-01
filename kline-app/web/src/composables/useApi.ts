import { ref } from 'vue'
import type { LogEntry } from '../types'

const logs = ref<LogEntry[]>([])

function pushLog(method: string, url: string, response: unknown, error = false) {
  const time = new Date().toLocaleTimeString()
  let text: string
  try {
    text = typeof response === 'string' ? response : JSON.stringify(response)
  } catch {
    text = String(response)
  }
  logs.value.unshift({ time, method, url, text, error })
  if (logs.value.length > 50) logs.value.pop()
}

async function apiCall(
  method: string,
  url: string,
  params: Record<string, unknown> | null = null,
) {
  try {
    const u = new URL(url, location.origin)
    if (params) {
      Object.entries(params).forEach(([k, v]) => u.searchParams.set(k, String(v)))
    }
    const res = await fetch(u, { method })
    const data = await res.json().catch(() => null)
    if (!res.ok) {
      pushLog(method, u.pathname + u.search, data || res.statusText, true)
      return null
    }
    pushLog(method, u.pathname + u.search, data)
    return data
  } catch (e) {
    pushLog(method, url, (e as Error).message, true)
    return null
  }
}

export function useApi() {
  return { logs, apiCall }
}
