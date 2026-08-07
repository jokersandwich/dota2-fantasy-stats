export const metricLabels = {
  kills: '击杀',
  deaths: '死亡',
  lastHitsAndDenies: '正反补',
  gpm: 'GPM',
  madstones: '狂石收集数量',
  towerKills: '摧毁防御塔',
  observerWards: '放置守卫',
  campsStacked: '堆叠野怪',
  runes: '拾取神符',
  watchers: '占领观察者',
  lotuses: '采集莲花',
  roshanKills: '击杀肉山',
  teamfightParticipation: '参与团战',
  stunDuration: '眩晕时间',
  tormentorKills: '消灭痛苦魔方',
  courierKills: '杀害信使',
  firstBlood: '第一滴血',
  smokes: '开雾次数',
} as const

export const roleLabels = {
  core: '核心',
  mid: '中路',
  support: '辅助',
} as const

export const roleFilterLabels = {
  all: '全部',
  ...roleLabels,
} as const

export const performanceLabels = {
  best: '最高表现',
  average: '平均表现',
} as const

export const uiLabels = {
  team: '队伍',
  players: '选手',
  role: '定位',
  games: '场次',
  roleFilter: '定位筛选',
  performanceMode: '数据类型',
  fantasyRankings: '梦幻挑战排行榜',
  selectColumnToSort: '点击任意列排序',
  noData: '暂无数据',
  averageSummary: '基于有效共同 EWC 场次的平均表现',
  bestSummary: '单场最高梦幻表现',
  valueLegend: '梦幻积分 / 原始值',
} as const
