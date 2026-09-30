"""业务模块目录：模块标识、中文名、台账列与状态序列的唯一来源。

概览卡片、下钻列表、各业务台账三处都从这里取模块名、列与状态，
保证「卡片数字」和「列出来的单子」说的是同一件事。
历史统计沿用 store.overview 里的既有口径（created/pending/abnormal 标记），
不在此目录中改动。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    label: str
    columns: tuple[str, ...]
    statuses: tuple[str, ...]


MODULES: tuple[ModuleSpec, ...] = (
    ModuleSpec(
        key="pipe",
        label="管段档案",
        columns=("管段编号", "管道类别", "起点井号", "终点井号", "管径规格", "管材类型", "埋设深度", "管段状态"),
        statuses=("待移交", "正常运行", "重点观测", "封闭施工"),
    ),
    ModuleSpec(
        key="manhole",
        label="检查井",
        columns=("井编号", "所在道路", "井盖类别", "井室深度", "井室尺寸", "上次清掏日", "责任班组", "检查井状态"),
        statuses=("待清掏", "正常使用", "井盖缺失", "已废弃"),
    ),
    ModuleSpec(
        key="valve",
        label="阀门井室",
        columns=("阀门编号", "阀门类别", "所在管段", "公称直径", "操作方向", "上次启闭日", "责任人员", "阀门状态"),
        statuses=("待启闭", "操作正常", "启闭卡涩", "已停用"),
    ),
    ModuleSpec(
        key="pumpstation",
        label="泵站设施",
        columns=("泵站编号", "泵站名称", "服务区域", "装机台数", "设计流量", "上次检修日", "值守方式", "泵站状态"),
        statuses=("待接管", "运行正常", "减量运行", "停运检修"),
    ),
    ModuleSpec(
        key="patrol",
        label="巡查任务",
        columns=("巡查单号", "巡查路线", "巡查人员", "巡查日期", "巡查里程", "发现问题数", "巡查时长", "巡查状态"),
        statuses=("待派发", "巡查中", "已提交", "已作废"),
    ),
    ModuleSpec(
        key="defect",
        label="缺陷登记",
        columns=("缺陷编号", "所在管段", "缺陷类别", "缺陷位置", "严重等级", "发现日期", "登记人员", "缺陷状态"),
        statuses=("待定级", "已定级", "处置中", "已闭环"),
    ),
    ModuleSpec(
        key="cctv",
        label="内窥检测",
        columns=("检测编号", "检测管段", "检测设备", "检测长度", "缺陷等级", "检测人员", "检测日期", "检测状态"),
        statuses=("待检测", "检测中", "已出具", "已退回"),
    ),
    ModuleSpec(
        key="repair",
        label="修复施工",
        columns=("修复单号", "关联缺陷", "修复方式", "承接单位", "开挖范围", "完成日期", "监理人员", "修复状态"),
        statuses=("待开工", "施工中", "待验收", "已完工"),
    ),
    ModuleSpec(
        key="pressure",
        label="压力监测",
        columns=("监测编号", "监测点位", "监测时段", "平均压力", "峰值压力", "越限次数", "采集人员", "监测状态"),
        statuses=("待采集", "采集正常", "压力越限", "已停测"),
    ),
    ModuleSpec(
        key="flow",
        label="流量监测",
        columns=("监测编号", "监测断面", "监测时段", "平均流量", "峰值流量", "累计流量", "采集人员", "监测状态"),
        statuses=("待采集", "采集正常", "流量异常", "已停测"),
    ),
    ModuleSpec(
        key="leak",
        label="泄漏排查",
        columns=("排查编号", "排查区域", "排查方式", "疑似点位", "检出数量", "排查人员", "排查日期", "排查状态"),
        statuses=("待排查", "排查中", "已处置", "已排除"),
    ),
    ModuleSpec(
        key="dredge",
        label="清淤疏浚",
        columns=("清淤单号", "清淤管段", "淤积厚度", "清淤长度", "清出泥量", "作业班组", "完成日期", "清淤状态"),
        statuses=("待安排", "清淤中", "已完成", "已取消"),
    ),
    ModuleSpec(
        key="material",
        label="养护材料",
        columns=("材料编号", "材料名称", "规格型号", "结存数量", "计量单位", "存放场地", "保管人员", "材料状态"),
        statuses=("正常可用", "临近不足", "已冻结", "已耗尽"),
    ),
    ModuleSpec(
        key="equip",
        label="养护机械",
        columns=("机械编号", "机械名称", "机械型号", "停放场地", "上次保养日", "下次保养日", "责任人", "机械状态"),
        statuses=("待保养", "可用", "保养中", "已报废"),
    ),
    ModuleSpec(
        key="traffic",
        label="占道许可",
        columns=("许可编号", "申请单位", "占道位置", "占道面积", "起止日期", "审批人员", "恢复期限", "许可状态"),
        statuses=("待审批", "已批准", "施工中", "已恢复"),
    ),
    ModuleSpec(
        key="complaint",
        label="公众诉求",
        columns=("诉求编号", "诉求来源", "诉求内容", "涉及管段", "受理人员", "处理措施", "办理期限", "诉求状态"),
        statuses=("待受理", "办理中", "已回复", "已关闭"),
    ),
    ModuleSpec(
        key="fund",
        label="养护资金",
        columns=("资金编号", "费用类别", "项目名称", "批复金额", "已用金额", "剩余额度", "审批人员", "资金状态"),
        statuses=("待审批", "已批复", "执行中", "已超支"),
    ),
    ModuleSpec(
        key="archive",
        label="管网档案",
        columns=("档案编号", "关联管段", "档案类别", "资料名称", "存放位置", "归档人员", "归档日期", "档案状态"),
        statuses=("待归档", "已归档", "待补充", "已作废"),
    ),
)

_BY_KEY: dict[str, ModuleSpec] = {spec.key: spec for spec in MODULES}

# 跨模块下钻时的通用列；单号取台账第一列的具体值。
CROSS_COLUMNS: tuple[str, ...] = ("业务模块", "单号", "业务名称", "状态", "待处理", "异常")


def module_keys() -> list[str]:
    return [spec.key for spec in MODULES]


def get_spec(module: str) -> ModuleSpec | None:
    return _BY_KEY.get(module)


def require_spec(module: str) -> ModuleSpec:
    spec = _BY_KEY.get(module)
    if spec is None:
        raise KeyError(module)
    return spec


def label_of(module: str) -> str:
    spec = _BY_KEY.get(module)
    return spec.label if spec else module
