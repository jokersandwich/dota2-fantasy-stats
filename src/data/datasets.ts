import datasetRegistry from '../../data/config/datasets/index.json'

export type Role = 'core' | 'mid' | 'support'

export type MetricKey =
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

export interface RoleMember {
  playerAccountId: number
  playerName: string
  position: 1 | 2 | 3 | 4 | 5
}

export interface BestMetricMember {
  playerAccountId: number
  playerName: string
  rawValue: number | null
  fantasyScore: number | null
}

export interface BestMetricValue {
  matchId: number
  members: BestMetricMember[]
  rawValue: number
  fantasyScore: number
}

export interface AverageMetricValue {
  rawValue: number
  fantasyScore: number
  validGames: number
}

export interface RoleMetric {
  best: BestMetricValue | null
  average: AverageMetricValue | null
}

export interface RoleUnit {
  teamId: number | null
  teamName: string
  role: Role
  members: RoleMember[]
  gamesPlayedTogether: number
  metrics: Record<MetricKey, RoleMetric>
}

export interface RoleRankingsPayload {
  schemaVersion: number
  datasetId: string
  rosterSourceId: string
  matchSourceId: string
  rulesetId: string
  generatedAt: string
  source: {
    leagueId: number
    matchesProcessed: number
    roleUnits: number
  }
  roleUnits: RoleUnit[]
}

export interface DatasetDescriptor {
  id: string
  roleRankingsUrl: string
}

interface DatasetResolution {
  datasetId: string
  invalidDatasetId: string | null
}

function assertRegistry(): void {
  if (datasetRegistry.schemaVersion !== 1) {
    throw new Error('Unsupported dataset registry schema')
  }
  if (!Array.isArray(datasetRegistry.datasets) || datasetRegistry.datasets.length === 0) {
    throw new Error('Dataset registry must contain at least one dataset')
  }
  if (new Set(datasetRegistry.datasets).size !== datasetRegistry.datasets.length) {
    throw new Error('Dataset registry contains duplicate IDs')
  }
  if (!datasetRegistry.datasets.includes(datasetRegistry.defaultDatasetId)) {
    throw new Error('Default dataset is not listed in the registry')
  }
}

assertRegistry()

export const DEFAULT_DATASET_ID = datasetRegistry.defaultDatasetId
export const DATASET_IDS = Object.freeze([...datasetRegistry.datasets])

const datasetIdSet = new Set<string>(DATASET_IDS)

export function isDatasetId(value: string | null): value is string {
  return value !== null && datasetIdSet.has(value)
}

function baseUrl(): string {
  const configured = import.meta.env.BASE_URL || '/'
  return configured.endsWith('/') ? configured : `${configured}/`
}

export function roleRankingsUrl(datasetId: string): string {
  return `${baseUrl()}data/datasets/${encodeURIComponent(datasetId)}/role-fantasy-rankings.json`
}

export const DATASETS: readonly DatasetDescriptor[] = Object.freeze(
  DATASET_IDS.map((id) => Object.freeze({ id, roleRankingsUrl: roleRankingsUrl(id) })),
)

export function resolveDatasetFromSearch(search: string): DatasetResolution {
  const requested = new URLSearchParams(search).get('dataset')
  if (requested === null || requested === '' || requested === DEFAULT_DATASET_ID) {
    return { datasetId: DEFAULT_DATASET_ID, invalidDatasetId: null }
  }
  if (isDatasetId(requested)) {
    return { datasetId: requested, invalidDatasetId: null }
  }
  return { datasetId: DEFAULT_DATASET_ID, invalidDatasetId: requested }
}

export function updateDatasetUrl(datasetId: string, mode: 'push' | 'replace'): void {
  const url = new URL(window.location.href)
  if (datasetId === DEFAULT_DATASET_ID) {
    url.searchParams.delete('dataset')
  } else {
    url.searchParams.set('dataset', datasetId)
  }
  window.history[mode === 'push' ? 'pushState' : 'replaceState']({}, '', url)
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function containsOnlyFiniteNumbers(value: unknown): boolean {
  if (typeof value === 'number') return Number.isFinite(value)
  if (Array.isArray(value)) return value.every(containsOnlyFiniteNumbers)
  if (isRecord(value)) return Object.values(value).every(containsOnlyFiniteNumbers)
  return true
}

function isRoleUnit(value: unknown): value is RoleUnit {
  if (!isRecord(value)) return false
  if (typeof value.teamName !== 'string') return false
  if (value.teamId !== null && !Number.isInteger(value.teamId)) return false
  if (value.role !== 'core' && value.role !== 'mid' && value.role !== 'support') return false
  if (!Array.isArray(value.members) || value.members.length === 0) return false
  if (!Number.isInteger(value.gamesPlayedTogether) || Number(value.gamesPlayedTogether) < 0) return false
  return isRecord(value.metrics)
}

export function validateRoleRankingsPayload(
  value: unknown,
  expectedDatasetId: string,
): RoleRankingsPayload {
  if (!isRecord(value)) throw new Error('Dataset payload must be an object')
  if (value.schemaVersion !== 1) throw new Error('Unsupported Role rankings schema')
  if (value.datasetId !== expectedDatasetId) throw new Error('Dataset payload identity mismatch')
  if (
    typeof value.rosterSourceId !== 'string' ||
    typeof value.matchSourceId !== 'string' ||
    typeof value.rulesetId !== 'string' ||
    typeof value.generatedAt !== 'string'
  ) {
    throw new Error('Dataset payload provenance is incomplete')
  }
  if (!isRecord(value.source)) throw new Error('Dataset payload source is missing')
  if (
    !Number.isInteger(value.source.leagueId) ||
    !Number.isInteger(value.source.matchesProcessed) ||
    !Number.isInteger(value.source.roleUnits)
  ) {
    throw new Error('Dataset payload source counts are invalid')
  }
  if (!Array.isArray(value.roleUnits) || !value.roleUnits.every(isRoleUnit)) {
    throw new Error('Dataset Role Units are invalid')
  }
  if (value.roleUnits.length !== value.source.roleUnits) {
    throw new Error('Dataset Role Unit count does not match its source metadata')
  }
  if (!containsOnlyFiniteNumbers(value)) {
    throw new Error('Dataset payload contains a non-finite number')
  }
  return value as unknown as RoleRankingsPayload
}

export function datasetDisplayName(
  datasetNames: Readonly<Record<string, string>>,
  datasetId: string,
): string {
  return datasetNames[datasetId] ?? datasetId
}
