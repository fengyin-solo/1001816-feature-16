<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">城市地下管网巡检养护平台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向城市给排水与燃气管网的管段建档、检查井阀门、巡查巡检、内窥检测、缺陷修复与压力流量监测的一体化养护后台。</span>
        <span class="head-user">
          <label class="identity-switch">
            值班身份：
            <select :value="identityKey" @change="switchIdentity($event)">
              <option value="admin">值班管理员（跨模块）</option>
              <option v-for="item in MODULES" :key="item.key" :value="`module:${item.key}`">
                {{ item.label }}账号
              </option>
            </select>
          </label>
          <span class="shift-text">· {{ store.shiftLabel }}</span>
        </span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { MODULES, type ModuleKey } from '@/config/modules'
import { useSessionStore, type Identity } from '@/stores/session'

const store = useSessionStore()
const router = useRouter()

/** 导航同样按身份过滤：模块账号看不到别的单位入口，越权只能靠手敲 URL，路由守卫会拦下。 */
const navItems = computed(() => [
  { label: '运营概览', path: '/' },
  ...MODULES.filter((item) => store.canAccessModule(item.key)).map((item) => ({
    label: item.label,
    path: `/${item.key}`,
  })),
])

const identityKey = computed(() =>
  store.isAdmin ? 'admin' : `module:${store.identity.module}`,
)

function switchIdentity(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  const identity: Identity =
    value === 'admin'
      ? { role: 'admin', module: null }
      : { role: 'module', module: value.replace('module:', '') as ModuleKey }
  store.switchIdentity(identity)
  // 切换后若停在无权页面，直接回运营页。
  if (!store.isAdmin && router.currentRoute.value.name !== 'dashboard') {
    void router.push('/')
  }
}
</script>

<style scoped>
.identity-switch { font-size: 13px; color: var(--muted); }
.identity-switch select { padding: 2px 6px; border: 1px solid var(--border); border-radius: 6px; }
.shift-text { margin-left: 8px; }
</style>
