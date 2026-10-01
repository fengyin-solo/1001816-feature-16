/** 统一请求封装：拼后端地址、自动带上当前值班账号、抛网络错误、给页脚留一句可读的说明。 */
const API_BASE = import.meta.env.VITE_API_BASE ?? ''
export const ACCOUNT_STORAGE_KEY = 'pipeline-session-account'

export function currentAccountId(): string {
  return localStorage.getItem(ACCOUNT_STORAGE_KEY) ?? 'admin'
}

export function request(path: string, init?: RequestInit): Promise<Response> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const headers = new Headers(init?.headers)
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  // 所有业务请求都带上当前账号；导出链接用 query 传，走 withAccount 参数
  if (!headers.has('X-Account-Id')) {
    headers.set('X-Account-Id', currentAccountId())
  }
  return fetch(url, { ...init, headers }).catch((error: unknown) => {
    const detail = error instanceof Error ? error.message : '请求未送达'
    throw new Error(`接口请求失败：${detail}`)
  })
}

/** 给 window.open 导出链接补账号参数（浏览器新窗口无法带请求头）。 */
export function withAccount(path: string): string {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}account_id=${encodeURIComponent(currentAccountId())}`
}

/** 读取后端错误里的可读原因（越权拦截等），解析不了再用兜底文案。 */
export async function errorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json()
    if (data && typeof data.detail === 'string') {
      return data.detail
    }
  } catch {
    // 非 JSON 响应时用兜底文案
  }
  return fallback
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await request(path)
  if (!response.ok) {
    throw new Error(await errorMessage(response, `接口返回 ${response.status}，数据未更新`))
  }
  return (await response.json()) as T
}
