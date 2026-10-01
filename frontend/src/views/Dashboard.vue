<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">
          汇总各业务模块的关键指标，先看总量再看异常。点每张卡片下的「查看单子」可按口径展开到具体单据，看完返回本页。
          当前口径：{{ caliber }}（台账与卡片取自同一份数据）。
        </p>
      </div>
      <div class="page-actions">
        <button class="btn" type="button" @click="loadOverview">重新拉取概览</button>
      </div>
    </header>

    <div v-if="loadError" class="drill-warn">
      <p>
        <span class="error-text">运营概览没拉到：{{ loadError }}</span>
        <button class="btn" type="button" @click="loadOverview">从这一步重新拉取</button>
      </p>
    </div>

    <div class="stat-row">
      <article v-for="card in cards" :key="card.key" class="stat-card" :class="{ clickable: card.key !== 'modules' }">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
        <span v-if="card.key === 'modules'" class="stat-sub">当前可见 {{ visibleModuleCount }} 个模块</span>
        <button v-else class="link drill-link" type="button" @click="openDrill(card.key, card.label)">
          查看单子（{{ session.isAdmin ? '可跨模块' : '仅本单位' }}）
        </button>
      </article>
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>
            <button class="link" type="button" @click="openModuleDrill(row, 'created', '今日新增')">{{ row.created }}</button>
          </td>
          <td>
            <button class="link" type="button" @click="openModuleDrill(row, 'pending', '待处理')">{{ row.pending }}</button>
          </td>
          <td>
            <button class="link" type="button" @click="openModuleDrill(row, 'abnormal', '异常量')">{{ row.abnormal }}</button>
          </td>
          <td>
            <RouterLink class="link" :to="modulePath(row.key)">打开{{ row.name }}台账</RouterLink>
          </td>
        </tr>
        <tr v-if="!moduleRows.length && !loadError">
          <td colspan="5" class="empty-state">没有可展示的模块台账</td>
        </tr>
      </tbody>
    </table>

    <section v-if="session.isAdmin" class="snapshot-block">
      <header class="snapshot-head">
        <h3>历史统计留档</h3>
        <button class="btn" type="button" :disabled="snapshotBusy" @click="leaveSnapshot">
          {{ snapshotBusy ? '留档中…' : '按当前口径留一份档' }}
        </button>
      </header>
      <p class="page-desc">历史统计按留档当时的口径冻结，之后台账变动不改写历史；用于月度对比。</p>
      <table class="data-table">
        <thead>
          <tr><th>留档日期</th><th>口径</th><th>说明</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
        </thead>
        <tbody>
          <tr v-for="snap in snapshots" :key="`${snap.date}-${snap.caliber}`">
            <td>{{ snap.date }}</td>
            <td>{{ snap.caliber }}</td>
            <td>{{ snap.note || '—' }}</td>
            <td>{{ cardOf(snap, 'created') }}</td>
            <td>{{ cardOf(snap, 'pending') }}</td>
            <td>{{ cardOf(snap, 'abnormal') }}</td>
          </tr>
          <tr v-if="snapshotError">
            <td colspan="6" class="error-text">{{ snapshotError }}</td>
          </tr>
        </tbody>
      </table>
    </section>
    <section v-else class="snapshot-block snapshot-locked">
      <h3>历史统计留档</h3>
      <p class="page-desc">历史留档含全部业务模块数据，仅值班管理员可调阅；业务模块账号如需对比请联系值班管理员。</p>
    </section>

    <DrillPanel
      v-if="drill"
      :kind="drill.kind"
      :card-label="drill.cardLabel"
      :module="drill.module"
      :module-name="drill.moduleName"
      @back="closeDrill"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson, request } from '@/api/client'
import { useSessionStore } from '@/stores/session'
import DrillPanel from '@/views/DrillPanel.vue'

type Card = { key: string; label: string; value: number }
type ModuleRow = { key: string; name: string; created: number; pending: number; abnormal: number }
type Overview = {
  cards: Card[]
  modules: ModuleRow[]
  caliber: string
}
type Snapshot = {
  date: string
  caliber: string
  note: string
  cards: Card[]
}

const session = useSessionStore()

const cards = ref<Card[]>([])
const moduleRows = ref<ModuleRow[]>([])
const caliber = ref('—')
const loadError = ref('')
const snapshots = ref<Snapshot[]>([])
const snapshotError = ref('')
const snapshotBusy = ref(false)

const drill = ref<{ kind: string; cardLabel: string; module: string | null; moduleName: string } | null>(null)

const visibleModuleCount = computed(() => moduleRows.value.length)

function cardOf(snap: Snapshot, key: string): number | string {
  return snap.cards.find((card) => card.key === key)?.value ?? '—'
}

function modulePath(key: string): string {
  return `/${key}`
}

async function loadOverview() {
  loadError.value = ''
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
    caliber.value = payload.caliber
  } catch (error) {
    // 拉不到时保留一句说明，不回退假数据，等用户从这一步重试
    cards.value = []
    moduleRows.value = []
    loadError.value = error instanceof Error ? error.message : '概览数据读取失败'
  }
}

function openDrill(kind: string, cardLabel: string) {
  // 业务账号的跨模块下钻会被后端拦下并说明原因，这里仍允许点击，让提示出现在面板里
  drill.value = { kind, cardLabel, module: null, moduleName: '全部业务模块' }
}

function openModuleDrill(row: ModuleRow, kind: string, cardLabel: string) {
  drill.value = { kind, cardLabel, module: row.key, moduleName: row.name }
}

function closeDrill() {
  drill.value = null
  // 看完返回运营页：刷新一次卡片，保证数字仍是当前台账
  void loadOverview()
}

async function loadSnapshots() {
  if (!session.isAdmin) {
    return
  }
  snapshotError.value = ''
  try {
    const payload = await fetchJson<{ items: Snapshot[] }>('/api/overview/snapshots')
    snapshots.value = payload.items
  } catch (error) {
    snapshotError.value = error instanceof Error ? error.message : '历史留档读取失败'
  }
}

async function leaveSnapshot() {
  snapshotBusy.value = true
  snapshotError.value = ''
  try {
    const response = await request('/api/overview/snapshots', { method: 'POST' })
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      throw new Error(data?.detail ?? '留档未成功')
    }
    await loadSnapshots()
  } catch (error) {
    snapshotError.value = error instanceof Error ? error.message : '留档未成功'
  } finally {
    snapshotBusy.value = false
  }
}

onMounted(async () => {
  await session.loadAccounts()
  await Promise.all([loadOverview(), loadSnapshots()])
})
</script>

<style scoped>
.stat-card { display: flex; flex-direction: column; gap: 4px; }
.stat-card.clickable { cursor: default; }
.stat-sub { font-size: 12px; color: var(--muted); }
.drill-link { font-size: 12px; align-self: flex-start; }
.drill-warn { border: 1px solid #f0c7c2; background: #fdf4f3; border-radius: 6px; padding: 8px 12px; margin-bottom: 12px; }
.drill-warn p { margin: 0; display: flex; gap: 12px; align-items: center; }
.snapshot-block { margin-top: 20px; }
.snapshot-head { display: flex; justify-content: space-between; align-items: center; }
.snapshot-head h3 { margin: 0; font-size: 15px; }
.snapshot-locked { border: 1px dashed var(--border); border-radius: 8px; padding: 10px 14px; background: #fafbfd; }
.snapshot-locked h3 { margin: 0 0 4px; font-size: 15px; }
</style>
