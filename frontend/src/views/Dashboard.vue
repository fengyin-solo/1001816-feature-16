<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常；每块数字下面那一行可点开，看它到底是哪些单子。</p>
      </div>
    </header>

    <div v-if="store.deniedNotice" class="notice-bar denied">
      <span>{{ store.deniedNotice }}</span>
      <button class="link" type="button" @click="store.clearDeniedNotice()">知道了</button>
    </div>

    <div v-if="identity" class="scope-bar">
      当前身份：<strong>{{ identity.role === 'admin' ? '值班管理员（可跨模块下钻）' : `业务模块账号 · ${identity.module_label}` }}</strong>
      <span v-if="identity.role !== 'admin'">——只能看到本单位经手的单子，跨模块点击会被拦下。</span>
    </div>

    <div v-if="errorMessage" class="state-box error-box">
      <p>{{ errorMessage }}</p>
      <button class="btn primary" type="button" :disabled="retrying" @click="loadOverview(true)">
        {{ retrying ? '正在重新拉取…' : '重试' }}
      </button>
    </div>

    <template v-else>
      <div class="stat-row">
        <article v-for="card in cards" :key="card.metric" class="stat-card">
          <span class="stat-label">{{ card.label }}</span>
          <strong class="stat-value">{{ card.value }}</strong>
          <button class="card-drill" type="button" @click="openDrill(card.metric)">
            <template v-if="card.metric === 'modules'">点开看由哪些模块组成</template>
            <template v-else>点开看组成这个数字的 {{ card.value }} 张单子（可再按状态挑一类）</template>
            <span class="arrow">→</span>
          </button>
        </article>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th>
            <th v-if="store.isAdmin">下钻</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in moduleRows"
            :key="row.key"
            :class="{ 'drillable-row': store.isAdmin }"
          >
            <td>
              <button
                v-if="store.isAdmin"
                class="link"
                type="button"
                :title="`仅看「${row.name}」模块`"
                @click="openModuleDrill(row.key)"
              >
                {{ row.name }}
              </button>
              <span v-else>{{ row.name }}</span>
            </td>
            <td>
              <button class="link" type="button" @click="openMetric(row.key, 'created')">{{ row.created }}</button>
            </td>
            <td>
              <button class="link" type="button" @click="openMetric(row.key, 'pending')">{{ row.pending }}</button>
            </td>
            <td>
              <button class="link" type="button" @click="openMetric(row.key, 'abnormal')">{{ row.abnormal }}</button>
            </td>
            <td v-if="store.isAdmin">
              <RouterLink class="link" :to="{ name: 'drill', params: { metric: 'pending' }, query: { module: row.key } }">
                看待处理/出错单子
              </RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
      <footer class="page-foot">
        <span>卡片数字与各业务台账取自同一份数据；历史统计仍按当时口径保留。</span>
      </footer>
    </template>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchJson } from '@/api/client'
import type { MetricKey } from '@/config/modules'
import { useSessionStore } from '@/stores/session'

type Card = { label: string; value: number; metric: MetricKey }
type ModuleRow = { key: string; name: string; created: number; pending: number; abnormal: number }
type Overview = {
  cards: Card[]
  modules: ModuleRow[]
  identity: { role: string; module: string | null; module_label: string | null }
}

const router = useRouter()
const store = useSessionStore()

const cards = ref<Card[]>([])
const moduleRows = ref<ModuleRow[]>([])
const identity = ref<Overview['identity'] | null>(null)
const errorMessage = ref('')
const retrying = ref(false)

/** 从失败的那一步接着再拉一次：错误态不再停在一片白板上，保留重试入口。 */
async function loadOverview(showStatus: boolean) {
  retrying.value = showStatus
  errorMessage.value = ''
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
    identity.value = payload.identity
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '运营概览拉取失败，请稍后重试'
  } finally {
    retrying.value = false
  }
}

function openDrill(metric: MetricKey) {
  void router.push({ name: 'drill', params: { metric } })
}

/** 管理员可指定单模块下钻；模块账号点其他模块的数字直接拦下并说明原因。 */
function openMetric(moduleKey: string, metric: MetricKey) {
  if (!store.isAdmin && store.identity.module !== moduleKey) {
    store.setDeniedNotice(
      `越权点击已拦下：业务模块账号只能查看本单位（${store.moduleLabel}）经手的单子，`
      + `不能下钻到「${moduleRows.value.find((row) => row.key === moduleKey)?.name ?? moduleKey}」。`,
    )
    return
  }
  void router.push({
    name: 'drill',
    params: { metric },
    query: store.isAdmin ? { module: moduleKey } : undefined,
  })
}

function openModuleDrill(moduleKey: string) {
  void router.push({ name: 'drill', params: { metric: 'pending' }, query: { module: moduleKey } })
}

onMounted(() => loadOverview(false))
</script>

<style scoped>
.notice-bar { display: flex; justify-content: space-between; gap: 12px; border-radius: 8px; padding: 8px 12px; margin-bottom: 12px; font-size: 13px; }
.notice-bar.denied { background: #fef3f2; border: 1px solid #f0a9a3; color: #b42318; }
.scope-bar { font-size: 12px; color: var(--muted); margin-bottom: 12px; }
.card-drill { display: block; margin-top: 8px; padding: 0; border: none; background: none; color: var(--brand); font-size: 12px; cursor: pointer; text-align: left; }
.card-drill .arrow { margin-left: 4px; }
.card-drill:hover { text-decoration: underline; }
.drillable-row { cursor: default; }
.state-box { background: #fff; border: 1px dashed var(--border); border-radius: 8px; padding: 24px; text-align: center; color: var(--muted); }
.error-box { color: #b42318; border-color: #f0a9a3; }
.error-box .btn { margin-top: 8px; }
</style>
