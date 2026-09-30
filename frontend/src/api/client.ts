/** 统一请求封装：拼后端地址、附带值班身份头、抛带后端说明的错误。 */
import { identityHeaders } from '@/stores/session'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export function request(path: string, init?: RequestInit): Promise<Response> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const headers = new Headers(init?.headers)
  headers.set('Content-Type', 'application/json')
  for (const [key, value] of Object.entries(identityHeaders())) {
    headers.set(key, value)
  }
  return fetch(url, { ...init, headers }).catch((error: unknown) => {
    const detail = error instanceof Error ? error.message : '请求未送达'
    throw new ApiError(`接口请求失败：${detail}（可点击“重试”从失败的那一步再拉一次）`, 0)
  })
}

/** 读取非 2xx 响应里的后端说明，没有时退回到调用方给的兜底文案。 */
export async function responseError(response: Response, fallback: string): Promise<ApiError> {
  let detail = ''
  try {
    const payload = await response.json()
    detail = typeof payload?.detail === 'string' ? payload.detail : ''
  } catch {
    detail = ''
  }
  return new ApiError(detail || `${fallback}（HTTP ${response.status}）`, response.status)
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await request(path)
  if (!response.ok) {
    throw await responseError(response, '接口数据未更新')
  }
  return (await response.json()) as T
}
