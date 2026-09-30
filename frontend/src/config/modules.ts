/** 业务模块目录：路由、中文名、概览卡片共用。后端 app/catalog.py 为同一口径。 */
export type ModuleKey =
  | 'pipe' | 'manhole' | 'valve' | 'pumpstation' | 'patrol' | 'defect'
  | 'cctv' | 'repair' | 'pressure' | 'flow' | 'leak' | 'dredge'
  | 'material' | 'equip' | 'traffic' | 'complaint' | 'fund' | 'archive'

export interface ModuleMeta {
  key: ModuleKey
  label: string
}

/** 顺序与后端目录一致；导航、权限过滤、身份切换下拉都用这一份。 */
export const MODULES: ModuleMeta[] = [
  { key: 'pipe', label: '管段档案' },
  { key: 'manhole', label: '检查井' },
  { key: 'valve', label: '阀门井室' },
  { key: 'pumpstation', label: '泵站设施' },
  { key: 'patrol', label: '巡查任务' },
  { key: 'defect', label: '缺陷登记' },
  { key: 'cctv', label: '内窥检测' },
  { key: 'repair', label: '修复施工' },
  { key: 'pressure', label: '压力监测' },
  { key: 'flow', label: '流量监测' },
  { key: 'leak', label: '泄漏排查' },
  { key: 'dredge', label: '清淤疏浚' },
  { key: 'material', label: '养护材料' },
  { key: 'equip', label: '养护机械' },
  { key: 'traffic', label: '占道许可' },
  { key: 'complaint', label: '公众诉求' },
  { key: 'fund', label: '养护资金' },
  { key: 'archive', label: '管网档案' },
]

const LABEL_BY_KEY = new Map(MODULES.map((item) => [item.key, item.label]))

export function moduleLabel(key: string | null | undefined): string {
  return (key && LABEL_BY_KEY.get(key as ModuleKey)) || ''
}

/** 概览四块卡片对应的下钻口径；与后端 METRIC_LABELS 保持一致。 */
export type MetricKey = 'modules' | 'created' | 'pending' | 'abnormal'

export const METRIC_LABELS: Record<MetricKey, string> = {
  modules: '业务模块',
  created: '今日新增',
  pending: '待处理',
  abnormal: '出错',
}
