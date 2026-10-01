import { defineStore } from 'pinia'

/**
 * 运营下钻状态：记住用户在每个卡片/模块里挑过的状态。
 * key 形如 pending（跨模块卡片，只存 __pending__/__abnormal__）
 * 或 repair:pending（某模块下某卡片，存该模块的业务状态）。
 * 状态只在“确定查看”后写入，退回运营页再进来仍然保留。
 */
const STORAGE_KEY = 'pipeline-drill-selections'

function load(): Record<string, string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as Record<string, string>) : {}
  } catch {
    return {}
  }
}

export const selectionKey = (kind: string, module: string | null): string =>
  module ? `${module}:${kind}` : kind

export const useDrillStore = defineStore('drill', {
  state: () => ({
    selections: load() as Record<string, string>,
  }),
  actions: {
    remember(kind: string, module: string | null, status: string | null) {
      const key = selectionKey(kind, module)
      if (status) {
        this.selections[key] = status
      } else {
        delete this.selections[key]
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.selections))
    },
    recall(kind: string, module: string | null): string | null {
      return this.selections[selectionKey(kind, module)] ?? null
    },
  },
})
