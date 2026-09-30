import { defineStore } from 'pinia'

import { MODULES, type ModuleKey } from '@/config/modules'

export type Role = 'admin' | 'module'

export interface Identity {
  role: Role
  module: ModuleKey | null
}

const STORAGE_KEY = 'operator-identity'

function loadIdentity(): Identity {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as { role?: string; module?: string | null }
      if (parsed.role === 'admin') {
        return { role: 'admin', module: null }
      }
      if (parsed.role === 'module' && MODULES.some((item) => item.key === parsed.module)) {
        return { role: 'module', module: parsed.module as ModuleKey }
      }
    }
  } catch {
    // 本地缓存损坏时退回默认值班管理员，不影响页面打开。
  }
  return { role: 'admin', module: null }
}

/** 供请求层读取：每次请求带上当前值班身份，后端据此做跨模块权限校验。 */
export function identityHeaders(): Record<string, string> {
  const identity = loadIdentity()
  const headers: Record<string, string> = { 'X-Operator-Role': identity.role }
  if (identity.role === 'module' && identity.module) {
    headers['X-Operator-Module'] = identity.module
  }
  return headers
}

export const useSessionStore = defineStore('session', {
  state: () => {
    const identity = loadIdentity()
    return {
      identity,
      operator: identity.role === 'admin' ? '值班管理员' : '',
      shiftLabel: '白班 08:00-20:00',
      scope: '城市地下管网巡检养护平台',
      // 被路由守卫拦下时的越权说明，运营页顶部展示一次。
      deniedNotice: '',
    }
  },
  getters: {
    isAdmin: (state) => state.identity.role === 'admin',
    canOperate: (state) => state.operator.length > 0 || state.identity.role === 'admin',
    /** 当前身份可进入的业务模块：管理员全部，模块账号只有本单位。 */
    allowedModules(state): ModuleKey[] {
      if (state.identity.role === 'admin') {
        return MODULES.map((item) => item.key)
      }
      return state.identity.module ? [state.identity.module] : []
    },
    moduleLabel(state): string {
      if (state.identity.role === 'admin') {
        return ''
      }
      return MODULES.find((item) => item.key === state.identity.module)?.label ?? ''
    },
  },
  actions: {
    switchIdentity(identity: Identity) {
      this.identity = identity
      this.operator = identity.role === 'admin' ? '值班管理员' : `${this.moduleLabel}账号`
      localStorage.setItem(STORAGE_KEY, JSON.stringify(identity))
      this.deniedNotice = ''
    },
    setDeniedNotice(message: string) {
      this.deniedNotice = message
    },
    clearDeniedNotice() {
      this.deniedNotice = ''
    },
    canAccessModule(moduleKey: string): boolean {
      return this.allowedModules.includes(moduleKey as ModuleKey)
    },
    setShift(label: string) {
      this.shiftLabel = label
    },
  },
})
