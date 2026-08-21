import { describe, expect, it } from 'vitest'
import { getEnvironment } from './environment'

describe('getEnvironment', () => {
  it('provides a valid API base URL', () => {
    expect(getEnvironment().apiBaseUrl).toMatch(/^https?:\/\//)
  })
})
