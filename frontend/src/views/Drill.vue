<template>
  <section class="page" data-view="drill">
    <header class="page-head">
      <div>
        <p class="page-desc">
          <RouterLink class="back-link" to="/">← 返回运营概览</RouterLink>
        </p>
        <h2>{{ title }}</h2>
        <p class="page-desc">{{ scopeText }}</p>
      </div>
      <div v-if="store.isAdmin && metric !== 'modules'" class="page-actions">
        <label class="filter-item">
          <span>业务模块（仅值班管理员可跨模块）</span>
          <select v-model="selectedModule" @change="reload(true)">
            <option value="">全部模块（跨模块下钻）</option>
            <option v-for="item in MODULES" :key="item.key" :value="item.key">{{ item.label }}</option>
          </select>
        </label>
      </div>
    </header>

    <div v-if="metric !== 'modules'" class="stat-row">
      <article class="stat-card">
        <span class="stat-label">卡片数字（同一口径）</span>
        <strong class="stat-value">{{ cardValue ?? total }}</strong>
        <span class="stat-hint">未挑状态时即列表条数{{ cardValue !== null && selectedStatus ? '；当前已按状态筛选' : '' }}</span>
      </article>
      <article class="stat-card">
        <span class="stat-label">列表条数</span>
        <strong class="stat-value">{{ total }}</strong>
        <span class="stat-hint">{{ selectedStatus ? `状态「${selectedStatus}」下的单子` : '与卡片数字一致' }}</span>
      </article>
    </div>

    <div v-if="facets.length" class="status-bar">
      <button
        class="chip"
        :class="{ active: !selectedStatus }"
        type="button"
        @click="pickStatus('')"
      >
        全部状态（{{ cardValue ?? total }}）
      </button>
      <button
        v-for="facet in facets"
        :key="facet.status"
        class="chip"
        :class="{ active: selectedStatus === facet.status }"
        type="button"
        @click="pickStatus(facet.status)"
      >
        {{ facet.status }}（{{ facet.count }}）
      </button>
    </div>

    <div v-if="loading" class="state-box">正在拉取{{ metricLabel }}的单子…</div>
    <div v-else-if="errorMessage" class="state-box error-box">
      <p>{{ errorMessage }}</p>
      <button class="btn primary" type="button" @click="reload(true)">重试</button>
    </div>

    <template v-else>
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column">{{ column }}</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="metric === 'modules'">
            <tr
              v-for="row in moduleRows"
              :key="row.key"
              class="drillable-row"
              :title="store.isAdmin ? '查看该模块这三块数字的单子' : '业务模块账号只能停留在本单位模块'"
              @click="openModule(row.key)"
            >
              <td>{{ row.name }}</td>
              <td>{{ row.created }}</td>
              <td>{{ row.pending }}</td>
              <td>{{ row.abnormal }}</td>
            </tr>
          </template>
          <template v-else>
            <tr v-for="row in items" :key="String(row.module ?? selectedModule ?? store.identity.module ?? 'all') + ':' + String(row.id)">
              <td v-for="column in columns" :key="column">{{ row[column] ?? '—' }}</td>
            </tr>
            <tr v-if="!items.length">
              <td :colspan="columns.length" class="empty-state">
                {{ selectedStatus ? `该口径下没有状态为「${selectedStatus}」的单子` : '该口径下暂无单子' }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <footer class="page-foot">
        <span>
          {{ metric === 'modules' ? `共 ${moduleRows.length} 个可见业务模块` : `共 ${total} 条单子` }}
          （数据与运营页卡片取自同一份台账）
        </span>
        <span v-if="selectedStatus" class="status-picked">已选状态：{{ selectedStatus }}（退出后仍保留）</span>
      </footer>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchJson, ApiError } from '@/api/client'
import { MODULES, moduleLabel, type MetricKey } from '@/config/modules'
import { useSessionStore } from '@/stores/session'

type Row = Record<string, string | number | boolean | null>
interface Facet { status: string; count: number }
interface DrillPayload {
  metric_label: string
  module: string | null
  cross_module: boolean
  columns: string[]
  facets: Facet[]
  card_value: number | null
  status: string | null
  items: Row[]
  total: number
}
interface ModuleRow {
  key: string
  name: string
  created: number
  pending: number
  abnormal: number
}
interface ModulesPayload {
  metric_label: string
  items: ModuleRow[]
  total: number
}

const route = useRoute()
const router = useRouter()
const store = useSessionStore()

const metric = computed<MetricKey>(() => String(route.params.metric ?? '') as MetricKey)
const metricLabel = computed(() => routeTitle(metric.value))

/** 状态选择持久化：按身份与口径区分；用户挑过的状态退出再进来仍保留。 */
function storageKey() {
  const scopeKey = store.isAdmin ? 'admin' : `module:${store.identity.module}`
  return `drill-status:${scopeKey}:${metric.value}`
}

const selectedStatus = ref('')
const selectedModule = ref('')
const columns = ref<string[]>([])
const facets = ref<Facet[]>([])
const items = ref<Row[]>([])
const moduleRows = ref<ModuleRow[]>([])
const total = ref(0)
const cardValue = ref<number | null>(null)
const loading = ref(true)
const errorMessage = ref('')

const title = computed(() => {
  if (metric.value === 'modules') return '业务模块下钻'
  const statusPart = selectedStatus.value ? ` · ${selectedStatus.value}` : ''
  return `${metricLabel.value}单子下钻${statusPart}`
})

const scopeText = computed(() => {
  if (metric.value === 'modules') {
    return store.isAdmin
      ? '值班管理员可跨模块查看；下面每个模块还能继续下钻到具体单子。'
      : `业务模块账号只能看到本单位（${store.moduleLabel}）经手的模块，不能跨模块。`
  }
  if (store.isAdmin) {
    return selectedModule.value
      ? `值班管理员视角：仅查看「${moduleLabel(selectedModule.value)}」模块。`
      : '值班管理员视角：跨模块汇总，列出的单子数与运营页卡片数字是同一口径。'
  }
  return `业务模块账号视角：仅本单位（${store.moduleLabel}）经手的单子；跨模块访问会被拦下。`
})

function routeTitle(value: MetricKey): string {
  return { modules: '业务模块', created: '今日新增', pending: '待处理', abnormal: '出错' }[value]
}

function pickStatus(status: string) {
  selectedStatus.value = status
  localStorage.setItem(storageKey(), status)
  void reload(true)
}

function openModule(moduleKey: string) {
  // 模块账号从「业务模块」下钻只能落在本单位；管理员可去任意模块。
  if (!store.isAdmin && store.identity.module !== moduleKey) {
    store.setDeniedNotice(
      `越权访问已拦下：业务模块账号只能查看本单位（${store.moduleLabel}）经手的单子。`,
    )
    return
  }
  void router.push({ name: 'drill', params: { metric: 'pending' }, query: { module: moduleKey } })
}

/** 从失败的那一步接着再拉一次：保留模块与状态选择，只重发请求，不清空页面。 */
async function reload(showLoading: boolean) {
  if (metric.value === 'modules') {
    await loadModules(showLoading)
    return
  }
  loading.value = showLoading
  errorMessage.value = ''
  const params = new URLSearchParams()
  if (store.isAdmin && selectedModule.value) params.set('module', selectedModule.value)
  // 先用状态全集校验记住的状态，非法状态直接清掉，避免后端 400 停在错误页。
  if (selectedStatus.value) {
    const allowed = new Set(facets.value.map((facet) => facet.status))
    if (allowed.size > 0 && !allowed.has(selectedStatus.value)) {
      selectedStatus.value = ''
      localStorage.setItem(storageKey(), '')
    } else {
      params.set('status', selectedStatus.value)
    }
  }
  try {
    const payload = await fetchJson<DrillPayload>(`/api/drill/${metric.value}?${params.toString()}`)
    columns.value = payload.columns
    facets.value = payload.facets
    items.value = payload.items
    total.value = payload.total
    cardValue.value = payload.card_value
  } catch (error) {
    // 记住的状态已不属于当前模块时后端返回 400：清掉后从失败的这一步自动再拉一次。
    if (error instanceof ApiError && error.status === 400 && selectedStatus.value) {
      selectedStatus.value = ''
      localStorage.setItem(storageKey(), '')
      loading.value = true
      await reload(true)
      return
    }
    // 403 等后端说明原样展示，让用户知道为什么被拦。
    errorMessage.value = error instanceof Error ? error.message : '单据列表拉取失败'
  } finally {
    loading.value = false
  }
}

async function loadModules(showLoading: boolean) {
  loading.value = showLoading
  errorMessage.value = ''
  try {
    const payload = await fetchJson<ModulesPayload>('/api/drill/modules')
    moduleRows.value = payload.items
    total.value = payload.total
    columns.value = ['业务模块', '今日新增', '待处理', '异常量']
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '模块列表拉取失败'
  } finally {
    loading.value = false
  }
}

watch(metric, () => {
  applyRouteState()
  void reload(true)
})

function applyRouteState() {
  const queryModule = String(route.query.module ?? '')
  selectedModule.value = store.isAdmin ? queryModule : (store.identity.module ?? '')
  selectedStatus.value = localStorage.getItem(storageKey()) ?? ''
  // 记住的状态在新模块/新口径下可能不存在；加载后按分面校验，不合法则清空重拉。
}

onMounted(() => {
  applyRouteState()
  void reload(false)
})
</script>

<style scoped>
.back-link { color: var(--brand); text-decoration: none; font-size: 13px; }
.stat-hint { display: block; color: var(--muted); font-size: 12px; margin-top: 4px; }
.status-bar { display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 12px; }
.chip { border: 1px solid var(--border); background: #fff; border-radius: 999px; padding: 4px 12px; font-size: 12px; cursor: pointer; }
.chip.active { background: var(--brand); border-color: var(--brand); color: #fff; }
.state-box { background: #fff; border: 1px dashed var(--border); border-radius: 8px; padding: 24px; text-align: center; color: var(--muted); }
.error-box { color: #b42318; border-color: #f0a9a3; }
.error-box .btn { margin-top: 8px; }
.drillable-row { cursor: pointer; }
.drillable-row:hover { background: #f0f6ff; }
.status-picked { color: var(--brand); }
.filter-item span { display: block; font-size: 12px; color: var(--muted); margin-bottom: 2px; }
.filter-item select { padding: 6px 8px; border: 1px solid var(--border); border-radius: 6px; }
</style>
