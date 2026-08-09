import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ti14Payload from '../data/generated/datasets/ti14/role-fantasy-rankings.json'
import App from './App'

function jsonResponse(payload: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => payload,
  } as Response
}

describe('App dataset switching', () => {
  beforeEach(() => {
    window.localStorage.setItem('dota2-fantasy-language', 'en')
    window.history.replaceState({}, '', '/')
  })

  it('switches EWC → TI14 → EWC while preserving filters, mode, sort, and language', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(ti14Payload)))
    const { container } = render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Best Performance' }))
    fireEvent.click(screen.getByRole('button', { name: 'Support' }))
    fireEvent.click(screen.getByTitle('First Blood'))

    fireEvent.click(screen.getByRole('button', { name: 'TI14' }))
    await waitFor(() => {
      expect(container.querySelector('.dataset-bar')?.getAttribute('data-active-dataset')).toBe('ti14')
    })

    expect(screen.getByRole('button', { name: 'Best Performance' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Support' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByTitle('First Blood').closest('th')?.getAttribute('aria-sort')).toBe('descending')
    expect(within(container.querySelector('.hero-stats')!).getByText('144')).toBeTruthy()
    expect(document.documentElement.lang).toBe('en')
    expect(new URL(window.location.href).searchParams.get('dataset')).toBe('ti14')

    fireEvent.click(screen.getByRole('button', { name: 'EWC 2026' }))
    await waitFor(() => {
      expect(container.querySelector('.dataset-bar')?.getAttribute('data-active-dataset')).toBe('ti15-ewc-2026')
    })
    expect(within(container.querySelector('.hero-stats')!).getByText('157')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Best Performance' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Support' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByTitle('First Blood').closest('th')?.getAttribute('aria-sort')).toBe('descending')
    expect(new URL(window.location.href).searchParams.has('dataset')).toBe(false)
  })

  it('shows a localized retryable error without clearing the EWC table', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({}, false, 404))
      .mockResolvedValueOnce(jsonResponse(ti14Payload))
    vi.stubGlobal('fetch', fetchMock)
    const { container } = render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'TI14' }))
    const alert = await screen.findByRole('alert')
    expect(alert.textContent).toContain('TI14 could not be loaded')
    expect(container.querySelector('.dataset-bar')?.getAttribute('data-active-dataset')).toBe('ti15-ewc-2026')
    expect(within(container.querySelector('.hero-stats')!).getByText('157')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await waitFor(() => {
      expect(container.querySelector('.dataset-bar')?.getAttribute('data-active-dataset')).toBe('ti14')
    })
    expect(screen.queryByRole('alert')).toBeNull()
    expect(within(container.querySelector('.hero-stats')!).getByText('144')).toBeTruthy()
  })

  it('keeps the selected language when switching to TI14', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(ti14Payload)))
    const { container } = render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Switch to Simplified Chinese' }))
    expect(document.documentElement.lang).toBe('zh-CN')
    expect(screen.getByText('赛事数据')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'TI14' }))
    await waitFor(() => {
      expect(container.querySelector('.dataset-bar')?.getAttribute('data-active-dataset')).toBe('ti14')
    })

    expect(document.documentElement.lang).toBe('zh-CN')
    expect(screen.getByText('统一使用 TI15 梦幻挑战规则评估 TI14 参赛选手的比赛表现。')).toBeTruthy()
    expect(within(container.querySelector('.hero-stats')!).getByText('144')).toBeTruthy()
  })

  it('retains sorting and horizontal table controls', () => {
    vi.stubGlobal('fetch', vi.fn())
    const scrollBySpy = vi.spyOn(HTMLElement.prototype, 'scrollBy')
    const { container } = render(<App />)

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
