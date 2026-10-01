<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">城市地下管网巡检养护平台</h1>
      <div class="account-box">
        <label class="account-label" for="account-switch">值班账号</label>
        <select id="account-switch" class="account-select" :value="store.accountId" @change="onSwitch">
          <option v-for="acc in store.accounts" :key="acc.id" :value="acc.id">
            {{ acc.label }}{{ acc.role === 'admin' ? '（可跨模块）' : '（仅本单位）' }}
          </option>
          <option v-if="!store.accounts.length" value="admin">值班管理员</option>
        </select>
        <p class="account-hint">
          {{ store.isAdmin ? '值班管理员：可跨模块下钻、调阅历史留档' : '业务模块账号：只能查看本单位经手的单子' }}
        </p>
      </div>
      <nav class="nav-list">
        <RouterLink v-for="item in visibleNavItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向城市给排水与燃气管网的管段建档、检查井阀门、巡查巡检、内窥检测、缺陷修复与压力流量监测的一体化养护后台。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView :key="store.accountId" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'

import { useSessionStore } from '@/stores/session'

const store = useSessionStore()

const allNavItems = [
  { label: '运营概览', path: '/', key: '__dashboard__' },
  { label: '管段档案', path: '/pipe', key: 'pipe' },
  { label: '检查井', path: '/manhole', key: 'manhole' },
  { label: '阀门井室', path: '/valve', key: 'valve' },
  { label: '泵站设施', path: '/pumpstation', key: 'pumpstation' },
  { label: '巡查任务', path: '/patrol', key: 'patrol' },
  { label: '缺陷登记', path: '/defect', key: 'defect' },
  { label: '内窥检测', path: '/cctv', key: 'cctv' },
  { label: '修复施工', path: '/repair', key: 'repair' },
  { label: '压力监测', path: '/pressure', key: 'pressure' },
  { label: '流量监测', path: '/flow', key: 'flow' },
  { label: '泄漏排查', path: '/leak', key: 'leak' },
  { label: '清淤疏浚', path: '/dredge', key: 'dredge' },
  { label: '养护材料', path: '/material', key: 'material' },
  { label: '养护机械', path: '/equip', key: 'equip' },
  { label: '占道许可', path: '/traffic', key: 'traffic' },
  { label: '公众诉求', path: '/complaint', key: 'complaint' },
  { label: '养护资金', path: '/fund', key: 'fund' },
  { label: '管网档案', path: '/archive', key: 'archive' },
]

// 业务账号侧边栏只保留运营概览与本单位模块，直接不点进别人的模块；
// 手工改地址越权仍会被后端拦下并返回原因。
const visibleNavItems = computed(() =>
  allNavItems.filter(
    (item) => store.isAdmin || item.key === '__dashboard__' || item.key === store.ownModule,
  ),
)

function onSwitch(event: Event) {
  store.switchAccount((event.target as HTMLSelectElement).value)
}

onMounted(() => {
  void store.loadAccounts()
})
</script>

<style scoped>
.account-box {
  background: #18243a;
  border: 1px solid #24324d;
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 14px;
}
.account-label { display: block; font-size: 11px; color: #93a4c0; margin-bottom: 4px; }
.account-select {
  width: 100%;
  background: #0f1a2c;
  color: #e5e7eb;
  border: 1px solid #2b3c5c;
  border-radius: 6px;
  padding: 5px 6px;
  font-size: 12px;
}
.account-hint { font-size: 11px; color: #8da2c4; margin: 6px 0 0; line-height: 1.5; }
</style>
