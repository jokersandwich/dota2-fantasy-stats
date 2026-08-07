import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import roleRankingsData from '../data/processed/role-fantasy-rankings.json'
import { useLanguage } from './i18n/useLanguage'
import type { Translation } from './i18n/translations'

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

function createColumns(translation: Translation): Column[] {
  return [
  { key: 'teamName', label: translation.table.team, align: 'left' },
  { key: 'members', label: translation.table.players, align: 'left' },
  { key: 'role', label: translation.table.role, align: 'center' },
  { key: 'gamesPlayedTogether', label: translation.table.games, align: 'right' },
  { key: 'kills', label: translation.metrics.kills, metric: 'kills', align: 'right' },
  { key: 'deaths', label: translation.metrics.deaths, metric: 'deaths', align: 'right' },
  { key: 'lastHitsAndDenies', label: translation.metrics.lastHitsAndDenies, metric: 'lastHitsAndDenies', align: 'right' },
  { key: 'gpm', label: translation.metrics.gpm, metric: 'gpm', align: 'right' },
  { key: 'madstones', label: translation.metrics.madstones, metric: 'madstones', align: 'right' },
  { key: 'towerKills', label: translation.metrics.towerKills, metric: 'towerKills', align: 'right' },
  { key: 'observerWards', label: translation.metrics.observerWards, metric: 'observerWards', align: 'right' },
  { key: 'campsStacked', label: translation.metrics.campsStacked, metric: 'campsStacked', align: 'right' },
  { key: 'runes', label: translation.metrics.runes, metric: 'runes', align: 'right' },
  { key: 'watchers', label: translation.metrics.watchers, metric: 'watchers', align: 'right' },
  { key: 'lotuses', label: translation.metrics.lotuses, metric: 'lotuses', align: 'right' },
  { key: 'roshanKills', label: translation.metrics.roshanKills, metric: 'roshanKills', align: 'right' },
  {
    key: 'teamfightParticipation',
    label: translation.metrics.teamfightParticipation,
    metric: 'teamfightParticipation',
    align: 'right',
  },
  { key: 'stunDuration', label: translation.metrics.stunDuration, metric: 'stunDuration', align: 'right' },
  { key: 'tormentorKills', label: translation.metrics.tormentorKills, metric: 'tormentorKills', align: 'right' },
  { key: 'courierKills', label: translation.metrics.courierKills, metric: 'courierKills', align: 'right' },
  { key: 'firstBlood', label: translation.metrics.firstBlood, metric: 'firstBlood', align: 'right' },
  { key: 'smokes', label: translation.metrics.smokes, metric: 'smokes', align: 'right' },
  ]
}

const teamLogoUrls: Record<number, string> = {
  9467224: 'https://cdn.steamusercontent.com/ugc/13052583756685508/22B0338D7E09FB2F021E5DB5BBEFFD170D5E5E1A/',
  8255888: 'https://cdn.steamusercontent.com/ugc/9995426432403529725/51E13136D4CCC8C7D8062861541A1D13B8ED87E0/',
  10182357: 'https://cdn.steamusercontent.com/ugc/10678669599334676082/E48827F4A163D4D02F817EA3C32166D5F1D5FC98/',
  9247354: 'https://cdn.steamusercontent.com/ugc/2314350571781870059/2B5C9FE9BA0A2DC303A13261444532AA08352843/',
  2163: 'https://steamcdn-a.akamaihd.net/apps/dota2/images/team_logos/2163.png',
  9823272: 'https://cdn.steamusercontent.com/ugc/12970505637628494427/B04C3358F4E815ADFC2F8B1B8BE3AB0CE75C8881/',
  8261500: 'https://cdn.steamusercontent.com/ugc/2402194226059610590/E3CF4B6C4B2CFB974A9B415141E4A37317AD4D80/',
  7119388: 'https://cdn.steamusercontent.com/ugc/1839179120711951766/CD7E0885CB527334205CC7885E9C101B7BC17702/',
  9824702: 'https://cdn.steamusercontent.com/ugc/11751543457229798134/1569CC553CB72963C8EC4C3F807EE50DA925BDC2/',
  10136357: 'https://cdn.steamusercontent.com/ugc/16959999218725724364/1D334B91A52606CA3E0027832D6F646E2A094391/',
  10149530: 'https://cdn.steamusercontent.com/ugc/14844266645370842778/47230D9640A722EAF06548C2EEB813ED4296AE3F/',
  5017210: 'https://cdn.steamusercontent.com/ugc/14326265454983833183/734A1D8A0938380A48221CDAE1AACB0C5C0AB585/',
  726228: 'https://steamcdn-a.akamaihd.net/apps/dota2/images/team_logos/726228.png',
  10150538: 'https://cdn.steamusercontent.com/ugc/10055782735581672481/2B2BCEA9CC05286D7164E4548A2EB64CDBC77F31/',
  9964962: 'https://cdn.steamusercontent.com/ugc/13245379764580870318/1048428BEFAC87EC1C64E15706A4758A173B5BFB/',
  2586976: 'https://steamcdn-a.akamaihd.net/apps/dota2/images/team_logos/2586976.png',
}

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
    useGrouping: false,
  }).format(value)
}

function formatRawValue(value: number, metric: MetricKey, performanceMode: PerformanceMode) {
  if (metric === 'teamfightParticipation' || (metric === 'firstBlood' && performanceMode === 'average')) {
    return `${formatNumber(value * 100, 1)}%`
  }
  return formatNumber(value, metric === 'gpm' ? 1 : 2)
}

function formatFantasyScore(value: number, scoreSuffix: string) {
  return `${formatNumber(value, 2)} ${scoreSuffix}`
}

function MetricCell({
  metric,
  metricKey,
  mode,
  scoreSuffix,
  unavailableLabel,
}: {
  metric: RoleMetric
  metricKey: MetricKey
  mode: PerformanceMode
  scoreSuffix: string
  unavailableLabel: string
}) {
  const value = getMetricDisplayValue(metric, mode)
  if (!value || !Number.isFinite(value.rawValue) || !Number.isFinite(value.fantasyScore)) {
    return <span className="unavailable-value" title={unavailableLabel}>—</span>
  }
  return (
    <span className="metric-value-stack">
      <span className="metric-fantasy-score">{formatFantasyScore(value.fantasyScore, scoreSuffix)}</span>
      <span className="metric-raw-value">{formatRawValue(value.rawValue, metricKey, mode)}</span>
    </span>
  )
}

function App() {
  const { language, toggleLanguage, translation } = useLanguage()
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('all')
  const [performanceMode, setPerformanceMode] = useState<PerformanceMode>('average')
  const [sortKey, setSortKey] = useState<SortKey>('gpm')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [tableScrollEdges, setTableScrollEdges] = useState({ canScrollLeft: false, canScrollRight: true })
  const tableScrollRef = useRef<HTMLDivElement>(null)

  const columns = useMemo(() => createColumns(translation), [translation])

  const visibleColumns = useMemo(
    () => columns.filter(
      (column) =>
        !column.metric ||
        payload.roleUnits.some((unit) => {
          const metric = unit.metrics[column.metric as MetricKey]
          return metric.best !== null || metric.average !== null
        }),
    ),
    [columns],
  )

  const metricColumns = useMemo(
    () => visibleColumns.filter(
      (column): column is Column & { metric: MetricKey } => Boolean(column.metric),
    ),
    [visibleColumns],
  )

  const updateTableScrollEdges = useCallback(() => {
    const scrollContainer = tableScrollRef.current
    if (!scrollContainer) return

    const maximumScrollLeft = scrollContainer.scrollWidth - scrollContainer.clientWidth
    const nextEdges = {
      canScrollLeft: scrollContainer.scrollLeft > 1,
      canScrollRight: scrollContainer.scrollLeft < maximumScrollLeft - 1,
    }

    setTableScrollEdges((currentEdges) =>
      currentEdges.canScrollLeft === nextEdges.canScrollLeft &&
      currentEdges.canScrollRight === nextEdges.canScrollRight
        ? currentEdges
        : nextEdges,
    )
  }, [])

  useEffect(() => {
    const scrollContainer = tableScrollRef.current
    if (!scrollContainer) return

    const animationFrame = window.requestAnimationFrame(updateTableScrollEdges)
    const resizeObserver = new ResizeObserver(updateTableScrollEdges)
    resizeObserver.observe(scrollContainer)
    const table = scrollContainer.querySelector('table')
    if (table) resizeObserver.observe(table)

    return () => {
      window.cancelAnimationFrame(animationFrame)
      resizeObserver.disconnect()
    }
  }, [language, updateTableScrollEdges, visibleColumns.length])

  const roleFilters: { key: RoleFilter; label: string }[] = [
    { key: 'all', label: translation.roleFilters.all },
    { key: 'core', label: translation.roleFilters.core },
    { key: 'mid', label: translation.roleFilters.mid },
    { key: 'support', label: translation.roleFilters.support },
  ]

  const performanceModes: { key: PerformanceMode; label: string }[] = [
    { key: 'best', label: translation.performance.best },
    { key: 'average', label: translation.performance.average },
  ]

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

  function scrollTable(direction: 'left' | 'right') {
    const scrollContainer = tableScrollRef.current
    if (!scrollContainer) return

    scrollContainer.scrollBy({
      left: (direction === 'left' ? -1 : 1) * Math.max(280, scrollContainer.clientWidth * 0.55),
      behavior: 'smooth',
    })
  }

  return (
    <main className={`app-shell lang-${language}`}>
      <header className="site-header">
        <div className="brand-mark" aria-hidden="true">TI</div>
        <div className="brand-copy">
          <p>{translation.brandTitle}</p>
          <span>{translation.leagueLabel} 19785</span>
        </div>
        <button
          type="button"
          className="language-switch"
          onClick={toggleLanguage}
          aria-label={translation.languageSwitchAria}
          title={translation.languageSwitchAria}
        >
          <span aria-hidden="true">文</span>
          {translation.languageSwitchText}
        </button>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">{translation.eyebrow}</p>
          <h1>{translation.heroTitle} <span>{translation.heroSubtitle}</span></h1>
          <p className="lede">{translation.heroDescription}</p>
        </div>
        <dl className="hero-stats">
          <div><dt>{translation.matches}</dt><dd>{payload.source.matchesProcessed}<span>/{payload.source.matchesProcessed}</span></dd></div>
          <div><dt>{translation.roleUnits}</dt><dd>{payload.roleUnits.length}</dd></div>
        </dl>
      </section>

      <section className="data-panel" aria-labelledby="player-table-title">
        <div className="table-toolbar">
          <div className="toolbar-controls">
            <div>
              <p className="section-label">{translation.roleFilter}</p>
              <div className="filter-group" role="group" aria-label={translation.roleFilterAria}>
                {roleFilters.map((filter) => (
                  <button
                    type="button"
                    key={filter.key}
                    className={`${roleFilter === filter.key ? 'active' : ''} role-filter-${filter.key}`}
                    onClick={() => setRoleFilter(filter.key)}
                    aria-pressed={roleFilter === filter.key}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="section-label">{translation.dataType}</p>
              <div className="filter-group mode-group" role="group" aria-label={translation.dataTypeAria}>
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
        </div>

        <div className="table-heading">
          <div>
            <p className="section-label">{translation.fantasyRankings}</p>
            <h2 id="player-table-title">{translation.performance[performanceMode]}</h2>
          </div>
          <p>{translation.selectColumnToSort} <span aria-hidden="true">↕</span></p>
        </div>

        <div className="table-scroll-shell">
          <div
            id="fantasy-rankings-scroll"
            ref={tableScrollRef}
            className="table-scroll"
            onScroll={updateTableScrollEdges}
          >
            <table className="player-table">
            <thead>
              <tr>
                {visibleColumns.map((column) => {
                  const active = sortKey === column.key
                  return (
                    <th
                      key={column.key}
                      scope="col"
                      className={`align-${column.align ?? 'left'} ${column.metric ? `metric-header metric-${column.metric}` : ''} ${active ? 'sorted' : ''}`}
                      aria-sort={active ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}
                    >
                      <button type="button" onClick={() => handleSort(column.key)} title={column.label}>
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
                <tr><td className="state-cell" colSpan={visibleColumns.length}>{translation.noData}</td></tr>
              ) : null}
              {visibleUnits.map((unit, index) => (
                <tr key={`${unit.teamId}-${unit.role}`}>
                  <td className={`team-cell ${sortKey === 'teamName' ? 'sorted-column' : ''}`}>
                    <span className="rank-number">{String(index + 1).padStart(2, '0')}</span>
                    <span className="team-identity">
                      {unit.teamId !== null && teamLogoUrls[unit.teamId] ? (
                        <img
                          className="team-logo"
                          src={teamLogoUrls[unit.teamId]}
                          alt=""
                          loading="lazy"
                          decoding="async"
                        />
                      ) : null}
                      <span className="team-name">{unit.teamName}</span>
                    </span>
                  </td>
                  <td className={`players-cell ${sortKey === 'members' ? 'sorted-column' : ''}`}>
                    <span className="member-names">{unit.members.map((member) => member.playerName).join(' & ')}</span>
                  </td>
                  <td className={`align-center role-cell ${sortKey === 'role' ? 'sorted-column' : ''}`}><span className={`role-badge role-${unit.role}`}>{translation.roles[unit.role]}</span></td>
                  <td className={`align-right games-cell ${sortKey === 'gamesPlayedTogether' ? 'sorted-column' : ''}`}>{unit.gamesPlayedTogether}</td>
                  {metricColumns.map((column) => (
                    <td key={column.key} className={`align-right metric-cell ${sortKey === column.metric ? 'sorted-column' : ''}`}>
                      <MetricCell
                        metric={unit.metrics[column.metric]}
                        metricKey={column.metric}
                        mode={performanceMode}
                        scoreSuffix={translation.scoreSuffix}
                        unavailableLabel={translation.unavailable}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
            </table>
          </div>
          <button
            type="button"
            className="table-scroll-control table-scroll-control-left"
            onClick={() => scrollTable('left')}
            disabled={!tableScrollEdges.canScrollLeft}
            aria-label={translation.scrollTableLeft}
            aria-controls="fantasy-rankings-scroll"
            title={translation.scrollTableLeft}
          >
            <span aria-hidden="true">‹</span>
          </button>
          <button
            type="button"
            className="table-scroll-control table-scroll-control-right"
            onClick={() => scrollTable('right')}
            disabled={!tableScrollEdges.canScrollRight}
            aria-label={translation.scrollTableRight}
            aria-controls="fantasy-rankings-scroll"
            title={translation.scrollTableRight}
          >
            <span aria-hidden="true">›</span>
          </button>
        </div>

        <footer className="table-footer">
          <span>{performanceMode === 'average' ? translation.averageSummary : translation.bestSummary}</span>
          <span>{translation.valueLegend}</span>
        </footer>
      </section>

      <footer className="site-footer">
        <span>{translation.footerTitle}</span>
        <span>{translation.dataSource}: OpenDota · {translation.league} {payload.source.leagueId}</span>
      </footer>
    </main>
  )
}

export default App
