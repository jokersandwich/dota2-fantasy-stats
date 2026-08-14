import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ti14Payload from '../../data/generated/datasets/ti14/role-fantasy-rankings.json'
import ti15Payload from '../../data/generated/datasets/ti15/role-fantasy-rankings.json'
import ewcPayload from '../../data/generated/datasets/ti15-ewc-2026/role-fantasy-rankings.json'
import { useDataset } from './useDataset'

function jsonResponse(payload: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => payload,
  } as Response
}

describe('useDataset', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/')
  })

  it('loads a valid TI14 deep link and keeps the query in the URL', async () => {
    window.history.replaceState({}, '', '/?dataset=ti14')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(ti14Payload)))

    const { result } = renderHook(() => useDataset())
    expect(result.current.activeDatasetId).toBe('ti15')

    await waitFor(() => expect(result.current.activeDatasetId).toBe('ti14'))
    expect(result.current.payload?.source.matchesProcessed).toBe(144)
    expect(new URL(window.location.href).searchParams.get('dataset')).toBe('ti14')
  })

  it('loads the explicit TI15 query from the public namespaced path', async () => {
    window.history.replaceState({}, '', '/?dataset=ti15')
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(ti15Payload))
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useDataset())

    await waitFor(() => expect(result.current.payload?.source.matchesProcessed).toBe(29))
    expect(result.current.activeDatasetId).toBe('ti15')
    expect(fetchMock).toHaveBeenCalledWith(
      '/data/datasets/ti15/role-fantasy-rankings.json',
      expect.any(Object),
    )
    expect(new URL(window.location.href).searchParams.get('dataset')).toBe('ti15')
  })

  it('normalizes an invalid query and loads the default dataset', async () => {
    window.history.replaceState({}, '', '/?dataset=unknown')
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(ti15Payload))
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useDataset())

    await waitFor(() => expect(result.current.payload?.source.matchesProcessed).toBe(29))
    expect(result.current.activeDatasetId).toBe('ti15')
    expect(fetchMock).toHaveBeenCalledWith(
      '/data/datasets/ti15/role-fantasy-rankings.json',
      expect.any(Object),
    )
    expect(new URL(window.location.href).searchParams.has('dataset')).toBe(false)
  })

  it('keeps TI15 active after a failure and succeeds when retried', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(ti15Payload))
      .mockResolvedValueOnce(jsonResponse({}, false, 404))
      .mockResolvedValueOnce(jsonResponse(ti14Payload))
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useDataset())

    await waitFor(() => expect(result.current.payload?.source.matchesProcessed).toBe(29))

    await act(async () => {
      await result.current.selectDataset('ti14')
    })
    expect(result.current.activeDatasetId).toBe('ti15')
    expect(result.current.payload?.source.matchesProcessed).toBe(29)
    expect(result.current.loadError).toEqual({ datasetId: 'ti14' })
    expect(new URL(window.location.href).searchParams.has('dataset')).toBe(false)

    await act(async () => {
      await result.current.retryDataset()
    })
    expect(result.current.activeDatasetId).toBe('ti14')
    expect(result.current.loadError).toBeNull()
    expect(new URL(window.location.href).searchParams.get('dataset')).toBe('ti14')
  })

  it('does not let a stale TI14 request override a later return to TI15', async () => {
    let resolveRequest!: (response: Response) => void
    const pendingResponse = new Promise<Response>((resolve) => {
      resolveRequest = resolve
    })
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(ti15Payload))
      .mockReturnValueOnce(pendingResponse)
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useDataset())

    await waitFor(() => expect(result.current.payload?.source.matchesProcessed).toBe(29))

    act(() => {
      void result.current.selectDataset('ti14')
    })
    await waitFor(() => expect(result.current.pendingDatasetId).toBe('ti14'))

    await act(async () => {
      await result.current.selectDataset('ti15')
    })
    resolveRequest(jsonResponse(ti14Payload))
    await act(async () => {
      await pendingResponse
    })

    expect(result.current.activeDatasetId).toBe('ti15')
    expect(result.current.payload?.source.matchesProcessed).toBe(29)
    expect(new URL(window.location.href).searchParams.has('dataset')).toBe(false)
  })

  it('follows browser back and forward navigation between cached datasets', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('ti15-ewc-2026')) return Promise.resolve(jsonResponse(ewcPayload))
      if (url.includes('ti14')) return Promise.resolve(jsonResponse(ti14Payload))
      return Promise.resolve(jsonResponse(ti15Payload))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useDataset())

    await waitFor(() => expect(result.current.payload?.source.matchesProcessed).toBe(29))

    await act(async () => {
      await result.current.selectDataset('ti14')
    })
    await act(async () => {
      await result.current.selectDataset('ti15-ewc-2026')
    })

    act(() => window.history.back())
    await waitFor(() => expect(result.current.activeDatasetId).toBe('ti14'))
    expect(new URL(window.location.href).searchParams.get('dataset')).toBe('ti14')

    act(() => window.history.back())
    await waitFor(() => expect(result.current.activeDatasetId).toBe('ti15'))
    expect(new URL(window.location.href).searchParams.has('dataset')).toBe(false)

    act(() => window.history.forward())
    await waitFor(() => expect(result.current.activeDatasetId).toBe('ti14'))
    expect(new URL(window.location.href).searchParams.get('dataset')).toBe('ti14')

    act(() => window.history.forward())
    await waitFor(() => expect(result.current.activeDatasetId).toBe('ti15-ewc-2026'))
    expect(new URL(window.location.href).searchParams.get('dataset')).toBe('ti15-ewc-2026')
  })
})
