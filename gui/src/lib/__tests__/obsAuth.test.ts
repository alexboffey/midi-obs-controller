import { describe, it, expect } from 'vitest'
import { sha256b64, obsAuth } from '../obsAuth.js'

describe('sha256b64', () => {
  it('produces the correct hash for "hello"', async () => {
    // echo -n "hello" | sha256sum → 2cf24dba5fb0a30e26e83b2ac5b9e29e...
    // base64(binary) → LPJNul+wow4m6DsqxbninhsWHlwfp0JecwQzYpOLmCQ=
    expect(await sha256b64('hello')).toBe('LPJNul+wow4m6DsqxbninhsWHlwfp0JecwQzYpOLmCQ=')
  })

  it('produces a 44-character base64 string (32 bytes → 44 base64 chars)', async () => {
    expect(await sha256b64('anything')).toHaveLength(44)
  })

  it('returns different hashes for different inputs', async () => {
    const a = await sha256b64('foo')
    const b = await sha256b64('bar')
    expect(a).not.toBe(b)
  })

  it('returns the same hash for the same input', async () => {
    const a = await sha256b64('reproducible')
    const b = await sha256b64('reproducible')
    expect(a).toBe(b)
  })
})

describe('obsAuth', () => {
  it('returns a 44-character base64 string', async () => {
    const result = await obsAuth('password', 'salt', 'challenge')
    expect(result).toHaveLength(44)
  })

  it('returns only valid base64 characters', async () => {
    const result = await obsAuth('password', 'salt', 'challenge')
    expect(result).toMatch(/^[A-Za-z0-9+/]+=*$/)
  })

  it('returns different results for different passwords', async () => {
    const a = await obsAuth('pass1', 'salt', 'challenge')
    const b = await obsAuth('pass2', 'salt', 'challenge')
    expect(a).not.toBe(b)
  })

  it('returns different results for different salts', async () => {
    const a = await obsAuth('pw', 'salt1', 'challenge')
    const b = await obsAuth('pw', 'salt2', 'challenge')
    expect(a).not.toBe(b)
  })

  it('returns different results for different challenges', async () => {
    const a = await obsAuth('pw', 'salt', 'challenge1')
    const b = await obsAuth('pw', 'salt', 'challenge2')
    expect(a).not.toBe(b)
  })

  it('is deterministic — same inputs produce same output', async () => {
    const a = await obsAuth('pw', 'salt', 'challenge')
    const b = await obsAuth('pw', 'salt', 'challenge')
    expect(a).toBe(b)
  })
})
