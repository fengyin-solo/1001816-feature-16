"""业务模块台账：模块别名、中文名、单号字段、状态口径的唯一登记处。

概览卡片、运营下钻接口与各业务模块页面都从这一份台账取模块定义，
避免运营页的数字与模块台账各说各话。历史统计的口径以留档时的快照为准，
改这里只影响当前口径，不回写历史快照。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleMeta:
    key: str  # 路由与数据仓库使用的模块别名
    name: str  # 中文名，与各路由 tags、侧边栏一致
    code_field: str  # 列表里用于展示的单号/编号字段
    status_field: str  # 列表里展示状态的字段
    statuses: tuple[str, ...]  # 该模块允许筛选的状态


# key 的顺序即模块展示顺序，与 frontend 侧边栏、routers/__init__.py 对齐
MODULES: tuple[ModuleMeta, ...] = (
    ModuleMeta("pipe", "管段档案", "管段编号", "管段状态", ("待移交", "正常运行", "重点观测", "封闭施工")),
    ModuleMeta("manhole", "检查井", "井编号", "检查井状态", ("待清掏", "正常使用", "井盖缺失", "已废弃")),
    ModuleMeta("valve", "阀门井室", "阀门编号", "阀门状态", ("待启闭", "操作正常", "启闭卡涩", "已停用")),
    ModuleMeta("pumpstation", "泵站设施", "泵站编号", "泵站状态", ("待接管", "运行正常", "减量运行", "停运检修")),
    ModuleMeta("patrol", "巡查任务", "巡查单号", "巡查状态", ("待派发", "巡查中", "已提交", "已作废")),
    ModuleMeta("defect", "缺陷登记", "缺陷编号", "缺陷状态", ("待定级", "已定级", "处置中", "已闭环")),
    ModuleMeta("cctv", "内窥检测", "检测编号", "检测状态", ("待检测", "检测中", "已出具", "已退回")),
    ModuleMeta("repair", "修复施工", "修复单号", "修复状态", ("待开工", "施工中", "待验收", "已完工")),
    ModuleMeta("pressure", "压力监测", "监测编号", "监测状态", ("待采集", "采集正常", "压力越限", "已停测")),
    ModuleMeta("flow", "流量监测", "监测编号", "监测状态", ("待采集", "采集正常", "流量异常", "已停测")),
    ModuleMeta("leak", "泄漏排查", "排查编号", "排查状态", ("待排查", "排查中", "已处置", "已排除")),
    ModuleMeta("dredge", "清淤疏浚", "清淤单号", "清淤状态", ("待安排", "清淤中", "已完成", "已取消")),
    ModuleMeta("material", "养护材料", "材料编号", "材料状态", ("正常可用", "临近不足", "已冻结", "已耗尽")),
    ModuleMeta("equip", "养护机械", "机械编号", "机械状态", ("待保养", "可用", "保养中", "已报废")),
    ModuleMeta("traffic", "占道许可", "许可编号", "许可状态", ("待审批", "已批准", "施工中", "已恢复")),
    ModuleMeta("complaint", "公众诉求", "诉求编号", "诉求状态", ("待受理", "办理中", "已回复", "已关闭")),
    ModuleMeta("fund", "养护资金", "资金编号", "资金状态", ("待审批", "已批复", "执行中", "已超支")),
    ModuleMeta("archive", "管网档案", "档案编号", "档案状态", ("待归档", "已归档", "待补充", "已作废")),
)

MODULE_BY_KEY: dict[str, ModuleMeta] = {meta.key: meta for meta in MODULES}


def get_module(key: str) -> ModuleMeta | None:
    return MODULE_BY_KEY.get(key)
