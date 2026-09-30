import { createRouter, createWebHistory } from 'vue-router'

import type { MetricKey, ModuleKey } from '@/config/modules'
import { MODULES } from '@/config/modules'
import { useSessionStore } from '@/stores/session'

import Dashboard from '@/views/Dashboard.vue'
const Drill = () => import('@/views/Drill.vue')
const Pipe = () => import('@/views/pipe/index.vue')
const Manhole = () => import('@/views/manhole/index.vue')
const Valve = () => import('@/views/valve/index.vue')
const Pumpstation = () => import('@/views/pumpstation/index.vue')
const Patrol = () => import('@/views/patrol/index.vue')
const Defect = () => import('@/views/defect/index.vue')
const Cctv = () => import('@/views/cctv/index.vue')
const Repair = () => import('@/views/repair/index.vue')
const Pressure = () => import('@/views/pressure/index.vue')
const Flow = () => import('@/views/flow/index.vue')
const Leak = () => import('@/views/leak/index.vue')
const Dredge = () => import('@/views/dredge/index.vue')
const Material = () => import('@/views/material/index.vue')
const Equip = () => import('@/views/equip/index.vue')
const Traffic = () => import('@/views/traffic/index.vue')
const Complaint = () => import('@/views/complaint/index.vue')
const Fund = () => import('@/views/fund/index.vue')
const Archive = () => import('@/views/archive/index.vue')

const VIEWS: Record<ModuleKey, () => Promise<unknown>> = {
  pipe: Pipe,
  manhole: Manhole,
  valve: Valve,
  pumpstation: Pumpstation,
  patrol: Patrol,
  defect: Defect,
  cctv: Cctv,
  repair: Repair,
  pressure: Pressure,
  flow: Flow,
  leak: Leak,
  dredge: Dredge,
  material: Material,
  equip: Equip,
  traffic: Traffic,
  complaint: Complaint,
  fund: Fund,
  archive: Archive,
}

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  {
    path: '/drill/:metric',
    name: 'drill',
    component: Drill,
    props: true,
  },
  ...MODULES.map((item) => ({
    path: `/${item.key}`,
    name: item.key,
    component: VIEWS[item.key],
  })),
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const DRILL_METRICS: MetricKey[] = ['modules', 'created', 'pending', 'abnormal']

/** 越权点击提前拦下：模块账号去别人的台账/模块页时退回运营页并说明原因。 */
router.beforeEach((to) => {
  const store = useSessionStore()
  const metric = to.name === 'drill' ? String(to.params.metric ?? '') : ''
  if (to.name === 'drill' && !DRILL_METRICS.includes(metric as MetricKey)) {
    store.setDeniedNotice(`下钻口径「${metric}」不存在，已退回运营概览。`)
    return { name: 'dashboard' }
  }
  const targetModule = String(to.name ?? '')
  if (MODULES.some((item) => item.key === targetModule) && !store.canAccessModule(targetModule)) {
    store.setDeniedNotice(
      `越权访问已拦下：业务模块账号只能查看本单位（${store.moduleLabel}）经手的单子，`
      + `「${MODULES.find((item) => item.key === targetModule)?.label ?? targetModule}」不在你的权限范围内。`,
    )
    return { name: 'dashboard' }
  }
  // 模块账号跨模块下钻（直接敲 URL /module=别人）也在此拦下，后端会再兜底一次。
  if (to.name === 'drill' && !store.isAdmin) {
    const requested = typeof to.query.module === 'string' ? to.query.module : ''
    if (requested && requested !== store.identity.module) {
      store.setDeniedNotice(
        `越权下钻已拦下：业务模块账号只能查看本单位（${store.moduleLabel}）经手的单子。`,
      )
      return { name: 'dashboard' }
    }
  }
  return true
})

export default router
