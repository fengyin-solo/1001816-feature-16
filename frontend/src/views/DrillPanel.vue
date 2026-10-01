<template>
  <div class="drill-mask" @click.self="$emit('back')">
    <section class="drill-panel">
      <header class="drill-head">
        <div>
          <h3>{{ cardLabel }} · {{ module ? moduleName : '全部业务模块' }}</h3>
          <p class="page-desc">
            按运营页这一块卡片的同一口径展开；卡片为
            <strong>{{ cardValueText }}</strong> 条，本次列出
            <strong>{{ data?.total ?? 0 }}</strong> 条
            <template v-if="statusFilter">
              ，当前只看「{{ module && data?.statuses ? statusFilter : crossStatusLabel }}」
            </template>
          </p>
        </div>
        <button class="btn" type="button" @click="$emit('back')">看完，返回运营页</button>
      </header>

      <div class="drill-filters">
        <label class="filter-item">
          <span>按状态挑一类</span>
          <select v-model="statusFilter" @change="onStatusChange">
            <option value="">全部{{ cardLabel }}单子</option>
            <template v-if="module && data?.statuses">
              <option v-for="s in data.statuses" :key="s" :value="s">{{ s }}</option>
            </template>
            <template v-else>
              <option value="__pending__">只看待处理</option>
              <option value="__abnormal__">只看出错</option>
            </template>
          </select>
        </label>
        <span v-if="loading" class="drill-hint">正在从台账取数…</span>
        <span v-else-if="fatalMessage" class="error-text">{{ fatalMessage }}</span>
        <button v-if="fatalMessage" class="btn" type="button" @click="reload()">从这一步重新拉取</button>
      </div>

      <div v-if="partialFailures.length" class="drill-warn">
        <template v-for="f in partialFailures" :key="f.module">
          <p>
            <span class="error-text">{{ f.name }}台账暂时拉取不到：{{ f.message }}</span>
            <button class="link" type="button" @click="retryFailedModule(f.module)">从「{{ f.name }}」这一步重新拉取</button>
          </p>
        </template>
        <p class="drill-hint">其余模块已列出；未拉到的模块可点按钮从那一步接着拉。</p>
      </div>

      <div v-if="moduleCounts.length > 1" class="drill-groups">
        <span v-for="g in moduleCounts" :key="g.key" class="group-chip" :class="{ failed: g.failed }">
          {{ g.name }} {{ g.failed ? '未拉到' : g.count }}
        </span>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th v-if="!module">业务模块</th>
            <th>单号</th>
            <th>当前状态</th>
            <th>待处理</th>
            <th>出错</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in items" :key="`${row.module}-${row.id}`">
            <td v-if="!module">{{ row.module_name }}</td>
            <td>{{ row.code || '—' }}</td>
            <td>{{ row.status || '—' }}</td>
            <td>
              <span :class="row.pending ? 'tag warn' : 'tag'">{{ row.pending ? '待处理' : '—' }}</span>
            </td>
            <td>
              <span :class="row.abnormal ? 'tag bad' : 'tag'">{{ row.abnormal ? '出错' : '—' }}</span>
            </td>
          </tr>
          <tr v-if="!loading && !items.length && !fatalMessage">
            <td :colspan="module ? 4 : 5" class="empty-state">
              {{ partialFailures.length ? '其余模块没有符合条件的单子' : '当前口径下没有单子' }}
            </td>
          </tr>
        </tbody>
      </table>

      <footer class="page-foot">
        <span>列出条数与「{{ cardLabel }}」卡片同口径{{ cardConsistent ? '' : '（部分模块未拉到，合计暂不可比）' }}</span>
        <button class="btn ghost" type="button" @click="reload()">重新拉取</button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { fetchJson } from '@/api/client'
import { useDrillStore } from '@/stores/drill'

type DrillRow = {
  id: number
  module: string
  module_name: string
  code: string
  status: string | null
  pending: boolean
  abnormal: boolean
}

type ModuleCount = { key: string; name: string; count: number; expected: number; failed: boolean }
type FailedModule = { module: string; name: string; message: string }

type DrillPayload = {
  kind: string
  module: string | null
  cross_module: boolean
  status: string | null
  status_label: string | null
  card_value: number | null
  total: number
  items: DrillRow[]
  module_counts: ModuleCount[]
  failed_modules: FailedModule[]
  statuses: string[] | null
}

const props = defineProps<{
  kind: string
  cardLabel: string
  module: string | null
  moduleName: string
}>()

const emit = defineEmits<{ back: [] }>()

const drillStore = useDrillStore()
const data = ref<DrillPayload | null>(null)
const loading = ref(false)
const fatalMessage = ref('')
const failedSet = ref<string[]>([])
// 弹层打开时先恢复用户上次挑过的状态
const statusFilter = ref<string>(drillStore.recall(props.kind, props.module) ?? '')

const items = computed(() => data.value?.items ?? [])
const moduleCounts = computed(() => data.value?.module_counts ?? [])
const partialFailures = computed(() => data.value?.failed_modules ?? [])
const cardValueText = computed(() => {
  if (!data.value) return '—'
  return data.value.card_value === null ? '部分未拉到' : String(data.value.card_value)
})
const cardConsistent = computed(() => data.value?.card_value !== null)
const crossStatusLabel = computed(() =>
  statusFilter.value === '__pending__' ? '待处理' : statusFilter.value === '__abnormal__' ? '出错' : '',
)

function buildQuery(failing: string[]): string {
  const params = new URLSearchParams({ kind: props.kind })
  if (props.module) {
    params.set('module', props.module)
  }
  if (statusFilter.value) {
    params.set('status', statusFilter.value)
  }
  if (failing.length) {
    params.set('fail', failing.join(','))
  }
  return `/api/drill?${params.toString()}`
}

async function load(failing: string[] = []) {
  loading.value = true
  fatalMessage.value = ''
  try {
    // 记住挑过的状态，退回运营页后再进来仍是这个选择
    drillStore.remember(props.kind, props.module, statusFilter.value || null)
    data.value = await fetchJson<DrillPayload>(buildQuery(failing))
    failedSet.value = data.value.failed_modules.map((item) => item.module)
  } catch (error) {
    // 整块拉不到（含越权拦截）时给一句说明，不允许白板
    data.value = null
    failedSet.value = []
    fatalMessage.value = error instanceof Error
      ? `${props.moduleName || '本块'}数据没拉到：${error.message}`
      : '本块业务拉不到数据，请重试'
  } finally {
    loading.value = false
  }
}

/** 整页/整块重拉：沿用当前状态筛选。 */
function reload() {
  void load([])
}

/** 从失败的那一步接着拉：保留其他已成功模块的结果，只补失败模块。 */
function retryFailedModule(moduleKey: string) {
  const remaining = failedSet.value.filter((key) => key !== moduleKey)
  void load(remaining)
}

function onStatusChange() {
  void load([])
}

watch(
  () => [props.kind, props.module],
  () => {
    statusFilter.value = drillStore.recall(props.kind, props.module) ?? ''
    void load([])
  },
)

void load([])
</script>

<style scoped>
.drill-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 32px 40px;
  z-index: 50;
  overflow: auto;
}
.drill-panel {
  background: #fff;
  border-radius: 10px;
  width: min(960px, 100%);
  padding: 18px 20px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.25);
}
.drill-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.drill-head h3 { margin: 0; font-size: 17px; }
.drill-filters { display: flex; align-items: flex-end; gap: 14px; margin: 10px 0; flex-wrap: wrap; }
.drill-hint { color: var(--muted); font-size: 12px; }
.drill-warn { border: 1px solid #f0c7c2; background: #fdf4f3; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; }
.drill-warn p { margin: 4px 0; font-size: 13px; display: flex; gap: 10px; align-items: center; }
.drill-groups { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.group-chip { font-size: 12px; background: #eef4ff; border: 1px solid #cfe0ff; border-radius: 999px; padding: 2px 10px; }
.group-chip.failed { background: #fdf4f3; border-color: #f0c7c2; color: #b42318; }
.tag { color: var(--muted); }
.tag.warn { color: #b54708; font-weight: 600; }
.tag.bad { color: #b42318; font-weight: 600; }
</style>
