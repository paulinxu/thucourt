import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

let csrfToken = ''
export function setCsrf(value: string) { csrfToken = value }
export function errorText(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map(errorText).join('；')
  if (value && typeof value === 'object') return Object.entries(value).map(([key, item]) => `${['error', 'detail', 'non_field_errors'].includes(key) ? '' : key + '：'}${errorText(item)}`).join('；')
  return '请求失败，请重试。'
}
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const isForm = body instanceof FormData
  const response = await fetch(`/api${path}`, {
    method, credentials: 'same-origin', headers: { ...(isForm ? {} : { 'Content-Type': 'application/json' }), ...(method !== 'GET' ? { 'X-CSRFToken': csrfToken } : {}) },
    body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
  })
  if (response.status === 204) return undefined as T
  let result: unknown
  try { result = await response.json() } catch { throw new Error('服务暂时不可用，请检查网络后重试。') }
  if (!response.ok) throw new Error(errorText(result))
  return result as T
}
export function useApi<T>(path: string, options?: { enabled?: boolean; poll?: number }) {
  return useQuery({ queryKey: [path], queryFn: () => api<T>(path), enabled: options?.enabled, refetchInterval: options?.poll, retry: 1 })
}
export function useAction() {
  const client = useQueryClient()
  return useMutation({ mutationFn: (fn: () => Promise<unknown>) => fn(), onSuccess: async () => { await client.invalidateQueries() } })
}
export function params(values: Record<string, string | number | boolean | undefined>) {
  return new URLSearchParams(Object.entries(values).filter(([, value]) => value !== undefined && value !== '').map(([key, value]) => [key, String(value)])).toString()
}
