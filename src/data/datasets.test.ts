import { describe, expect, it } from 'vitest'
import ti14Payload from '../../data/generated/datasets/ti14/role-fantasy-rankings.json'
import {
  DATASET_IDS,
  DEFAULT_DATASET_ID,
  datasetDisplayName,
  resolveDatasetFromSearch,
  roleRankingsUrl,
  validateRoleRankingsPayload,
} from './datasets'

describe('dataset registry', () => {
  it('keeps TI15 as the default and preserves registry order', () => {
    expect(DEFAULT_DATASET_ID).toBe('ti15')
    expect(DATASET_IDS).toEqual(['ti15', 'ti15-ewc-2026', 'ti14'])
    expect(new Set(DATASET_IDS).size).toBe(DATASET_IDS.length)
  })

  it('resolves valid, missing, and invalid URL queries safely', () => {
    expect(resolveDatasetFromSearch('')).toEqual({
      datasetId: 'ti15',
      invalidDatasetId: null,
    })
    expect(resolveDatasetFromSearch('?dataset=ti14')).toEqual({
      datasetId: 'ti14',
      invalidDatasetId: null,
    })
    expect(resolveDatasetFromSearch('?dataset=ti15-ewc-2026')).toEqual({
      datasetId: 'ti15-ewc-2026',
      invalidDatasetId: null,
    })
    expect(resolveDatasetFromSearch('?dataset=missing')).toEqual({
      datasetId: 'ti15',
      invalidDatasetId: 'missing',
    })
  })

  it('builds a conventional public Role rankings path for any registry ID', () => {
    expect(roleRankingsUrl('ti14')).toBe('/data/datasets/ti14/role-fantasy-rankings.json')
    expect(roleRankingsUrl('ti15')).toBe('/data/datasets/ti15/role-fantasy-rankings.json')
  })

  it('accepts the real TI14 payload and rejects identity mismatches', () => {
    expect(validateRoleRankingsPayload(ti14Payload, 'ti14').source.matchesProcessed).toBe(144)
    expect(() => validateRoleRankingsPayload(ti14Payload, 'ti15-ewc-2026')).toThrow(
      'Dataset payload identity mismatch',
    )
  })

  it('falls back to a dataset ID when a translated label is not present', () => {
    expect(datasetDisplayName({ ti14: 'TI14' }, 'ti14')).toBe('TI14')
    expect(datasetDisplayName({ ti14: 'TI14' }, 'ti15')).toBe('ti15')
  })
})
