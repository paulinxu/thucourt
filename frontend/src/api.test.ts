import { describe, expect, it } from 'vitest'
import { errorText, params } from './api'

describe('frontend API helpers', () => {
  it('serializes only present filter values', () => {
    expect(params({ area: 2, date: '2026-10-31', empty: '', missing: undefined, mine: false })).toBe('area=2&date=2026-10-31&mine=false')
  })
  it('turns nested DRF errors into readable Chinese text', () => {
    expect(errorText({ error: { detail: '无权访问。', field: ['格式不正确。'] } })).toContain('无权访问。')
    expect(errorText(['请求失败', '请重试'])).toBe('请求失败；请重试')
  })
})
