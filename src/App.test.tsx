import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ti14Payload from '../data/generated/datasets/ti14/role-fantasy-rankings.json'
import ti15Payload from '../data/generated/datasets/ti15/role-fantasy-rankings.json'
import ewcPayload from '../data/generated/datasets/ti15-ewc-2026/role-fantasy-rankings.json'
import App from './App'

function jsonResponse(payload: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => payload,
  } as Response
}

function datasetFetch(input: RequestInfo | URL): Promise<Response> {
  const url = String(input)
  if (url.includes('ti15-ewc-2026')) return Promise.resolve(jsonResponse(ewcPayload))
  if (url.includes('ti14')) return Promise.resolve(jsonResponse(ti14Payload))
  return Promise.resolve(jsonResponse(ti15Payload))
}

function chooseDataset(container: HTMLElement, datasetName: string) {
  fireEvent.click(container.querySelector<HTMLButtonElement>('.hero-dataset-trigger')!)
  expect(screen.getByRole('listbox')).toBeTruthy()
  fireEvent.click(screen.getByRole('option', { name: datasetName }))
}

describe('App dataset switching', () => {
  beforeEach(() => {
    window.localStorage.setItem('dota2-fantasy-language', 'en')
    window.history.replaceState({}, '', '/')
  })

  it('switches TI15 → EWC → TI14 → TI15 while preserving filters, mode, sort, and language', async () => {
    vi.stubGlobal('fetch', vi.fn(datasetFetch))
    const { container } = render(<App />)

    await waitFor(() => {
      expect(within(container.querySelector('.hero-stats')!).getByText('29')).toBeTruthy()
    })
    expect(screen.getByRole('button', { name: 'Best Performance' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Average Performance' }).getAttribute('aria-pressed')).toBe('false')
    fireEvent.click(screen.getByRole('button', { name: 'Support' }))
    fireEvent.click(screen.getByTitle('First Blood'))

    chooseDataset(container, 'EWC')
    await waitFor(() => {
      expect(container.querySelector('.hero-dataset-card')?.getAttribute('data-active-dataset')).toBe('ti15-ewc-2026')
    })
    expect(within(container.querySelector('.hero-stats')!).getByText('157')).toBeTruthy()

    chooseDataset(container, 'TI14')
    await waitFor(() => {
      expect(container.querySelector('.hero-dataset-card')?.getAttribute('data-active-dataset')).toBe('ti14')
    })
    expect(within(container.querySelector('.hero-stats')!).getByText('144')).toBeTruthy()

    chooseDataset(container, 'TI15')
    await waitFor(() => {
      expect(container.querySelector('.hero-dataset-card')?.getAttribute('data-active-dataset')).toBe('ti15')
    })
    expect(within(container.querySelector('.hero-stats')!).getByText('29')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Best Performance' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Support' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByTitle('First Blood').closest('th')?.getAttribute('aria-sort')).toBe('descending')
    expect(document.documentElement.lang).toBe('en')
    expect(new URL(window.location.href).searchParams.has('dataset')).toBe(false)
  })

  it('shows a localized retryable error without clearing the TI15 table', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(ti15Payload))
      .mockResolvedValueOnce(jsonResponse({}, false, 404))
      .mockResolvedValueOnce(jsonResponse(ti14Payload))
    vi.stubGlobal('fetch', fetchMock)
    const { container } = render(<App />)

    await waitFor(() => expect(within(container.querySelector('.hero-stats')!).getByText('29')).toBeTruthy())
    chooseDataset(container, 'TI14')
    const alert = await screen.findByRole('alert')
    expect(alert.textContent).toContain('TI14 could not be loaded')
    expect(container.querySelector('.hero-dataset-card')?.getAttribute('data-active-dataset')).toBe('ti15')
    expect(within(container.querySelector('.hero-stats')!).getByText('29')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await waitFor(() => {
      expect(container.querySelector('.hero-dataset-card')?.getAttribute('data-active-dataset')).toBe('ti14')
    })
    expect(screen.queryByRole('alert')).toBeNull()
    expect(within(container.querySelector('.hero-stats')!).getByText('144')).toBeTruthy()
  })

  it('keeps the selected language when switching to TI14', async () => {
    vi.stubGlobal('fetch', vi.fn(datasetFetch))
    const { container } = render(<App />)

    await waitFor(() => expect(within(container.querySelector('.hero-stats')!).getByText('29')).toBeTruthy())
    fireEvent.click(screen.getByRole('button', { name: 'Switch to Simplified Chinese' }))
    expect(document.documentElement.lang).toBe('zh-CN')
    expect(screen.getByRole('button', { name: '最高分' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: '平均分' }).getAttribute('aria-pressed')).toBe('false')
    expect(screen.getByText('赛事数据')).toBeTruthy()

    chooseDataset(container, 'TI14')
    await waitFor(() => {
      expect(container.querySelector('.hero-dataset-card')?.getAttribute('data-active-dataset')).toBe('ti14')
    })

    expect(document.documentElement.lang).toBe('zh-CN')
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('TI15 梦幻挑战选手数据')
    expect(screen.getByText('使用 TI15 梦幻挑战规则评估选手在TI15、EWC、TI14的比赛表现。')).toBeTruthy()
    expect(within(container.querySelector('.hero-stats')!).getByText('144')).toBeTruthy()
  })

  it('renders a logo for every TI15, EWC, and TI14 Role Unit', async () => {
    vi.stubGlobal('fetch', vi.fn(datasetFetch))
    const { container } = render(<App />)

    await waitFor(() => expect(container.querySelectorAll('.team-cell')).toHaveLength(48))
    expect(container.querySelectorAll('.team-cell img')).toHaveLength(48)
    const ti15LogoSources = new Set(
      Array.from(container.querySelectorAll<HTMLImageElement>('.team-cell img'), (image) => image.getAttribute('src')),
    )
    expect(ti15LogoSources.size).toBe(16)
    expect(Array.from(ti15LogoSources).every((source) => source?.startsWith('/assets/team-logos/ti15/'))).toBe(true)

    chooseDataset(container, 'EWC')
    await waitFor(() => {
      expect(container.querySelector('.hero-dataset-card')?.getAttribute('data-active-dataset')).toBe('ti15-ewc-2026')
    })
    expect(container.querySelectorAll('.team-cell img')).toHaveLength(48)
    expect(
      Array.from(container.querySelectorAll<HTMLImageElement>('.team-cell img')).every((image) =>
        image.getAttribute('src')?.startsWith('https://'),
      ),
    ).toBe(true)

    chooseDataset(container, 'TI14')
    await waitFor(() => {
      expect(container.querySelector('.hero-dataset-card')?.getAttribute('data-active-dataset')).toBe('ti14')
    })
    expect(container.querySelectorAll('.team-cell img')).toHaveLength(48)
  })

  it('shows all three registry datasets in selector order', async () => {
    vi.stubGlobal('fetch', vi.fn(datasetFetch))
    const { container } = render(<App />)

    await waitFor(() => expect(within(container.querySelector('.hero-stats')!).getByText('29')).toBeTruthy())
    fireEvent.click(container.querySelector<HTMLButtonElement>('.hero-dataset-trigger')!)
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(3)
    expect(options[0].textContent).toContain('TI15')
    expect(options[1].textContent).toBe('EWC')
    expect(options[2].textContent).toBe('TI14')
    expect(options.every((option) => !(option as HTMLButtonElement).disabled)).toBe(true)
  })

  it('retains sorting and horizontal table controls', async () => {
    vi.stubGlobal('fetch', vi.fn(datasetFetch))
    const scrollBySpy = vi.spyOn(HTMLElement.prototype, 'scrollBy')
    const { container } = render(<App />)

    await waitFor(() => expect(container.querySelectorAll('.team-cell')).toHaveLength(48))
    expect(screen.getByTitle('Kills').closest('th')?.getAttribute('aria-sort')).toBe('descending')
    const firstBloodHeader = screen.getByTitle('First Blood').closest('th')
    fireEvent.click(screen.getByTitle('First Blood'))
    expect(firstBloodHeader?.getAttribute('aria-sort')).toBe('descending')
    fireEvent.click(screen.getByTitle('First Blood'))
    expect(firstBloodHeader?.getAttribute('aria-sort')).toBe('ascending')

    const scrollContainer = container.querySelector<HTMLElement>('.table-scroll')!
    Object.defineProperties(scrollContainer, {
      clientWidth: { configurable: true, value: 1000 },
      scrollWidth: { configurable: true, value: 2000 },
      scrollLeft: { configurable: true, value: 0, writable: true },
    })
    fireEvent.scroll(scrollContainer)
    fireEvent.click(screen.getByRole('button', { name: 'Scroll data table right' }))
    expect(scrollBySpy).toHaveBeenCalledWith({ left: 550, behavior: 'smooth' })

    expect(container.querySelector('.player-table')).toBeTruthy()
    expect(container.querySelector('.team-cell')).toBeTruthy()
    expect(container.querySelector('.players-cell')).toBeTruthy()
    expect(container.querySelector('.role-cell')).toBeTruthy()
    expect(container.querySelector('.games-cell')).toBeTruthy()
  })
})
