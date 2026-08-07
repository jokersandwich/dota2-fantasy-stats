import { useMemo, useState } from 'react'
import roleRankingsData from '../data/processed/role-fantasy-rankings.json'

type PerformanceMode = 'best' | 'average'
type Role = 'core' | 'mid' | 'support'
type RoleFilter = 'all' | Role
type SortDirection = 'asc' | 'desc'

type MetricKey =
  | 'kills'
  | 'deaths'
  | 'lastHitsAndDenies'
  | 'gpm'
  | 'madstones'
  | 'towerKills'
  | 'observerWards'
  | 'campsStacked'
  | 'runes'
  | 'watchers'
  | 'lotuses'
  | 'roshanKills'
  | 'teamfightParticipation'
  | 'stunDuration'
  | 'tormentorKills'
  | 'courierKills'
  | 'firstBlood'
  | 'smokes'

type SortKey = 'teamName' | 'members' | 'role' | 'gamesPlayedTogether' | MetricKey

interface RoleMember {
  playerAccountId: number
  playerName: string
  position: 1 | 2 | 3 | 4 | 5
}

interface BestMetricMember {
  playerAccountId: number
  playerName: string
  rawValue: number | null
  fantasyScore: number | null
}

interface BestMetricValue {
  matchId: number
  members: BestMetricMember[]
  rawValue: number
  fantasyScore: number
}

interface AverageMetricValue {
  rawValue: number
  fantasyScore: number
  validGames: number
}

interface RoleMetric {
  best: BestMetricValue | null
  average: AverageMetricValue | null
}

interface RoleUnit {
  teamId: number | null
  teamName: string
  role: Role
  members: RoleMember[]
  gamesPlayedTogether: number
  metrics: Record<MetricKey, RoleMetric>
}

interface RoleRankingsPayload {
  schemaVersion: number
  generatedAt: string
  source: {
    leagueId: number
    matchesProcessed: number
    roleUnits: number
  }
  roleUnits: RoleUnit[]
}

interface Column {
  key: SortKey
  label: string
  shortLabel?: string
  metric?: MetricKey
  align?: 'left' | 'right' | 'center'
}

const payload = roleRankingsData as unknown as RoleRankingsPayload

const columns: Column[] = [
  { key: 'teamName', label: 'Team', align: 'left' },
  { key: 'members', label: 'Players', align: 'left' },
  { key: 'role', label: 'Role', align: 'center' },
  { key: 'gamesPlayedTogether', label: 'Games', align: 'right' },
  { key: 'kills', label: 'Kills', metric: 'kills', align: 'right' },
  { key: 'deaths', label: 'Deaths', metric: 'deaths', align: 'right' },
  { key: 'lastHitsAndDenies', label: 'Last Hits + Denies', shortLabel: 'LH+D', metric: 'lastHitsAndDenies', align: 'right' },
  { key: 'gpm', label: 'GPM', metric: 'gpm', align: 'right' },
  { key: 'madstones', label: 'Madstones', shortLabel: 'Mad', metric: 'madstones', align: 'right' },
  { key: 'towerKills', label: 'Tower Kills', shortLabel: 'Towers', metric: 'towerKills', align: 'right' },
  { key: 'observerWards', label: 'Observer Wards', shortLabel: 'Obs', metric: 'observerWards', align: 'right' },
  { key: 'campsStacked', label: 'Camps Stacked', shortLabel: 'Stacks', metric: 'campsStacked', align: 'right' },
  { key: 'runes', label: 'Runes', metric: 'runes', align: 'right' },
  { key: 'watchers', label: 'Watchers', metric: 'watchers', align: 'right' },
  { key: 'lotuses', label: 'Lotuses', metric: 'lotuses', align: 'right' },
  { key: 'roshanKills', label: 'Roshan Kills', shortLabel: 'Roshan', metric: 'roshanKills', align: 'right' },
  {
    key: 'teamfightParticipation',
    label: 'Teamfight Participation',
    shortLabel: 'TFP',
    metric: 'teamfightParticipation',
    align: 'right',
  },
  { key: 'stunDuration', label: 'Stun Duration', shortLabel: 'Stuns', metric: 'stunDuration', align: 'right' },
  { key: 'tormentorKills', label: 'Tormentor Kills', shortLabel: 'Tormentor', metric: 'tormentorKills', align: 'right' },
  { key: 'courierKills', label: 'Courier Kills', shortLabel: 'Courier', metric: 'courierKills', align: 'right' },
  { key: 'firstBlood', label: 'First Blood', shortLabel: 'FB', metric: 'firstBlood', align: 'right' },
  { key: 'smokes', label: 'Smokes', metric: 'smokes', align: 'right' },
]

const metricColumns = columns.filter((column): column is Column & { metric: MetricKey } => Boolean(column.metric))

const roleFilters: { key: RoleFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'core', label: 'Core' },
  { key: 'mid', label: 'Mid' },
  { key: 'support', label: 'Support' },
]

const performanceModes: { key: PerformanceMode; label: string }[] = [
  { key: 'best', label: '最高表现' },
  { key: 'average', label: '平均表现' },
]

const roleOrder: Record<Role, number> = { core: 1, mid: 2, support: 3 }

function getMetricDisplayValue(metric: RoleMetric, performanceMode: PerformanceMode) {
  return metric[performanceMode]
}

function metricSortValue(unit: RoleUnit, metric: MetricKey, performanceMode: PerformanceMode) {
  return getMetricDisplayValue(unit.metrics[metric], performanceMode)?.fantasyScore ?? null
}

function sortValue(unit: RoleUnit, key: SortKey, performanceMode: PerformanceMode): string | number | null {
  if (key === 'teamName') return unit.teamName
  if (key === 'members') return unit.members.map((member) => member.playerName).join(' ')
  if (key === 'role') return roleOrder[unit.role]
  if (key === 'gamesPlayedTogether') return unit.gamesPlayedTogether
  return metricSortValue(unit, key, performanceMode)
}

function formatNumber(value: number, maximumFractionDigits = 2) {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits,
  }).format(value)
}

function formatRawValue(value: number, metric: MetricKey, performanceMode: PerformanceMode) {
  if (metric === 'teamfightParticipation' || (metric === 'firstBlood' && performanceMode === 'average')) {
    return `${formatNumber(value * 100, 1)}%`
  }
  return formatNumber(value, metric === 'gpm' ? 1 : 2)
}

function formatFantasyScore(value: number) {
  return `${formatNumber(value, 2)} pts`
}

function MetricCell({ metric, metricKey, mode }: { metric: RoleMetric; metricKey: MetricKey; mode: PerformanceMode }) {
  const value = getMetricDisplayValue(metric, mode)
  if (!value || !Number.isFinite(value.rawValue) || !Number.isFinite(value.fantasyScore)) {
    return <span className="unavailable-value">—</span>
  }
  return (
    <span className="metric-value-stack">
      <span className="metric-raw-value">{formatRawValue(value.rawValue, metricKey, mode)}</span>
      <span className="metric-fantasy-score">{formatFantasyScore(value.fantasyScore)}</span>
    </span>
  )
}

function App() {
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('all')
  const [performanceMode, setPerformanceMode] = useState<PerformanceMode>('average')
  const [sortKey, setSortKey] = useState<SortKey>('gpm')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const visibleUnits = useMemo(() => {
    const direction = sortDirection === 'asc' ? 1 : -1
    return payload.roleUnits
      .filter((unit) => roleFilter === 'all' || unit.role === roleFilter)
      .sort((left, right) => {
        const leftValue = sortValue(left, sortKey, performanceMode)
        const rightValue = sortValue(right, sortKey, performanceMode)
        if (leftValue === null && rightValue === null) return 0
        if (leftValue === null) return 1
        if (rightValue === null) return -1
        if (typeof leftValue === 'string' && typeof rightValue === 'string') {
          return leftValue.localeCompare(rightValue, 'en', { sensitivity: 'base' }) * direction
        }
        const comparison = (Number(leftValue) - Number(rightValue)) * direction
        if (comparison !== 0) return comparison
        const teamComparison = left.teamName.localeCompare(right.teamName, 'en', { sensitivity: 'base' })
        return teamComparison || roleOrder[left.role] - roleOrder[right.role]
      })
  }, [performanceMode, roleFilter, sortDirection, sortKey])

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDirection((current) => (current === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortKey(key)
    setSortDirection(key === 'teamName' || key === 'members' || key === 'role' ? 'asc' : 'desc')
  }

  return (
    <main className="app-shell">
      <header className="site-header">
        <div className="brand-mark" aria-hidden="true">TI</div>
        <div className="brand-copy">
          <p>THE INTERNATIONAL 2026 / FANTASY LAB</p>
          <span>OpenDota League 19785</span>
        </div>
        <div className="header-status"><span aria-hidden="true" /> EWC DATA</div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">PLAYER PERFORMANCE INDEX</p>
          <h1>TI15 Fantasy <span>— EWC 2026 Player Stats</span></h1>
          <p className="lede">TI15 Fantasy Role Units evaluated exclusively through their Esports World Cup 2026 match data.</p>
        </div>
        <dl className="hero-stats">
          <div><dt>Matches</dt><dd>{payload.source.matchesProcessed}<span>/{payload.source.matchesProcessed}</span></dd></div>
          <div><dt>Role Units</dt><dd>{payload.roleUnits.length}</dd></div>
          <div><dt>Default view</dt><dd className="text-value">AVG / GAME</dd></div>
        </dl>
      </section>

      <section className="data-panel" aria-labelledby="player-table-title">
        <div className="table-toolbar">
          <div className="toolbar-controls">
            <div>
              <p className="section-label">ROLE GROUP</p>
              <div className="filter-group" role="group" aria-label="Filter role units">
                {roleFilters.map((filter) => (
                  <button
                    type="button"
                    key={filter.key}
                    className={roleFilter === filter.key ? 'active' : ''}
                    onClick={() => setRoleFilter(filter.key)}
                    aria-pressed={roleFilter === filter.key}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="section-label">PERFORMANCE</p>
              <div className="filter-group mode-group" role="group" aria-label="选择表现模式">
                {performanceModes.map((mode) => (
                  <button
                    type="button"
                    key={mode.key}
                    className={performanceMode === mode.key ? 'active' : ''}
                    onClick={() => setPerformanceMode(mode.key)}
                    aria-pressed={performanceMode === mode.key}
                  >
                    {mode.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="toolbar-meta">
            <span className="live-dot" aria-hidden="true" />
            <strong>{visibleUnits.length}</strong> UNITS
          </div>
        </div>

        <div className="table-heading">
          <div>
            <p className="section-label">ROLE LEADERBOARD</p>
            <h2 id="player-table-title">{performanceMode === 'average' ? 'Average performance' : 'Best performance'}</h2>
          </div>
          <p>Select any column to sort <span aria-hidden="true">↕</span></p>
        </div>

        <div className="table-scroll">
          <table className="player-table">
            <thead>
              <tr>
                {columns.map((column) => {
                  const active = sortKey === column.key
                  return (
                    <th
                      key={column.key}
                      scope="col"
                      className={`align-${column.align ?? 'left'} ${column.metric ? 'metric-header' : ''} ${active ? 'sorted' : ''}`}
                      aria-sort={active ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}
                    >
                      <button type="button" onClick={() => handleSort(column.key)}>
                        <span className="label-full">{column.label}</span>
                        <span className="label-short">{column.shortLabel ?? column.label}</span>
                        <span className="sort-indicator" aria-hidden="true">{active ? (sortDirection === 'asc' ? '↑' : '↓') : '↕'}</span>
                      </button>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              {visibleUnits.length === 0 ? (
                <tr><td className="state-cell" colSpan={columns.length}>No Role Units available.</td></tr>
              ) : null}
              {visibleUnits.map((unit, index) => (
                <tr key={`${unit.teamId}-${unit.role}`}>
                  <td className="team-cell"><span className="rank-number">{String(index + 1).padStart(2, '0')}</span>{unit.teamName}</td>
                  <td>
                    <div className="member-list">
                      {unit.members.map((member) => (
                        <span className="member-entry" key={member.playerAccountId}>
                          <strong>{member.playerName}</strong>
                          <small>P{member.position}</small>
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="align-center"><span className={`role-badge role-${unit.role}`}>{unit.role.toUpperCase()}</span></td>
                  <td className="align-right games-cell">{unit.gamesPlayedTogether}</td>
                  {metricColumns.map((column) => (
                    <td key={column.key} className={`align-right metric-cell ${column.metric === 'gpm' ? 'accent-value' : ''}`}>
                      <MetricCell metric={unit.metrics[column.metric]} metricKey={column.metric} mode={performanceMode} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <footer className="table-footer">
          <span>{performanceMode === 'average' ? 'AVERAGE VALUES ACROSS VALID SHARED EWC GAMES' : 'BEST SINGLE-GAME FANTASY PERFORMANCE'}</span>
          <span>RAW VALUE / BASE FANTASY POINTS</span>
        </footer>
      </section>

      <footer className="site-footer">
        <span>TI15 FANTASY / EWC 2026</span>
        <span>DATA: OPENDOTA · LEAGUE {payload.source.leagueId}</span>
      </footer>
    </main>
  )
}

export default App
