import { defineStore } from 'pinia'

import { ACCOUNT_STORAGE_KEY, fetchJson } from '@/api/client'

export type AccountOption = {
  id: string
  label: string
  role: 'admin' | 'module'
  module: string | null
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    accountId: localStorage.getItem(ACCOUNT_STORAGE_KEY) ?? 'admin',
    accounts: [] as AccountOption[],
    shiftLabel: '白班 08:00-20:00',
    scope: '城市地下管网巡检养护平台',
  }),
  getters: {
    account(state): AccountOption | undefined {
      return state.accounts.find((item) => item.id === state.accountId)
    },
    operator(): string {
      return this.account?.label ?? '未登录'
    },
    isAdmin(): boolean {
      return this.account?.role === 'admin'
    },
    /** 当前账号可访问的模块 key；管理员不限，业务账号只有本单位一个 */
    ownModule(): string | null {
      return this.account?.module ?? null
    },
    canOperate(): boolean {
      return this.accountId.length > 0
    },
  },
  actions: {
    async loadAccounts() {
      if (this.accounts.length) {
        return
      }
      try {
        const payload = await fetchJson<{ items: AccountOption[] }>('/api/accounts')
        this.accounts = payload.items
        // 本地记住的账号若已失效，回到值班管理员
        if (!this.accounts.some((item) => item.id === this.accountId)) {
          this.switchAccount('admin')
        }
      } catch {
        // 账号清单拉不到时不锁死页面，保留默认管理员身份，业务请求会再报具体原因
      }
    },
    switchAccount(id: string) {
      this.accountId = id
      localStorage.setItem(ACCOUNT_STORAGE_KEY, id)
    },
    setShift(label: string) {
      this.shiftLabel = label
    },
  },
})
