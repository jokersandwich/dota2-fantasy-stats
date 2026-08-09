import { useCallback, useEffect, useRef, useState } from 'react'
import {
  DEFAULT_DATASET_ID,
  isDatasetId,
  resolveDatasetFromSearch,
  roleRankingsUrl,
  updateDatasetUrl,
  validateRoleRankingsPayload,
  type RoleRankingsPayload,
} from '../data/datasets'

export interface DatasetLoadError {
  datasetId: string
}

type HistoryMode = 'none' | 'push' | 'replace'

export function useDataset(defaultPayloadValue: unknown) {
  const defaultPayload = validateRoleRankingsPayload(defaultPayloadValue, DEFAULT_DATASET_ID)
  const cacheRef = useRef(new Map<string, RoleRankingsPayload>([[DEFAULT_DATASET_ID, defaultPayload]]))
  const abortControllerRef = useRef<AbortController | null>(null)
  const requestIdRef = useRef(0)
  const activeDatasetIdRef = useRef(DEFAULT_DATASET_ID)

  const [activeDatasetId, setActiveDatasetId] = useState(DEFAULT_DATASET_ID)
  const [payload, setPayload] = useState(defaultPayload)
  const [pendingDatasetId, setPendingDatasetId] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<DatasetLoadError | null>(null)

  const commitDataset = useCallback(
    (datasetId: string, nextPayload: RoleRankingsPayload, historyMode: HistoryMode) => {
      activeDatasetIdRef.current = datasetId
      setActiveDatasetId(datasetId)
      setPayload(nextPayload)
      setPendingDatasetId(null)
      setLoadError(null)
      if (historyMode !== 'none') updateDatasetUrl(datasetId, historyMode)
    },
    [],
  )

  const requestDataset = useCallback(
    async (datasetId: string, historyMode: HistoryMode) => {
      if (!isDatasetId(datasetId)) {
        const fallback = cacheRef.current.get(DEFAULT_DATASET_ID)!
        commitDataset(DEFAULT_DATASET_ID, fallback, 'replace')
        return false
      }

      abortControllerRef.current?.abort()
      const requestId = requestIdRef.current + 1
      requestIdRef.current = requestId

      const cached = cacheRef.current.get(datasetId)
      if (cached) {
        commitDataset(datasetId, cached, historyMode)
        return true
      }

      const controller = new AbortController()
      abortControllerRef.current = controller
      setPendingDatasetId(datasetId)
      setLoadError(null)

      try {
        const response = await fetch(roleRankingsUrl(datasetId), {
          signal: controller.signal,
          headers: { Accept: 'application/json' },
        })
        if (!response.ok) throw new Error(`Dataset request failed with HTTP ${response.status}`)
        const nextPayload = validateRoleRankingsPayload(await response.json(), datasetId)
        if (requestId !== requestIdRef.current) return false
        cacheRef.current.set(datasetId, nextPayload)
        commitDataset(datasetId, nextPayload, historyMode)
        return true
      } catch (error) {
        if (requestId !== requestIdRef.current || controller.signal.aborted) return false
        setPendingDatasetId(null)
        setLoadError({ datasetId })
        if (historyMode === 'none') updateDatasetUrl(activeDatasetIdRef.current, 'replace')
        return false
      }
    },
    [commitDataset],
  )

  const selectDataset = useCallback(
    async (datasetId: string) => {
      if (datasetId === activeDatasetIdRef.current && pendingDatasetId === null) {
        setLoadError(null)
        updateDatasetUrl(datasetId, 'replace')
        return true
      }
      return requestDataset(datasetId, 'push')
    },
    [pendingDatasetId, requestDataset],
  )

  const retryDataset = useCallback(async () => {
    if (!loadError) return false
    return requestDataset(loadError.datasetId, 'push')
  }, [loadError, requestDataset])

  useEffect(() => {
    const syncFromLocation = () => {
      const resolution = resolveDatasetFromSearch(window.location.search)
      if (resolution.invalidDatasetId !== null) {
        updateDatasetUrl(DEFAULT_DATASET_ID, 'replace')
      }
      if (resolution.datasetId === activeDatasetIdRef.current) {
        setPendingDatasetId(null)
        setLoadError(null)
        return
      }
      void requestDataset(resolution.datasetId, 'none')
    }

    syncFromLocation()
    window.addEventListener('popstate', syncFromLocation)
    return () => {
      window.removeEventListener('popstate', syncFromLocation)
      abortControllerRef.current?.abort()
      requestIdRef.current += 1
    }
  }, [requestDataset])

  return {
    activeDatasetId,
    payload,
    pendingDatasetId,
    loadError,
    selectDataset,
    retryDataset,
  }
}
