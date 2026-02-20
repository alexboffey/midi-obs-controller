import { describe, it, expect } from 'vitest'
import { noteName } from '../noteNames.js'

describe('noteName', () => {
  it('maps 60 → C4 (middle C)', () => expect(noteName(60)).toBe('C4'))
  it('maps 48 → C3',           () => expect(noteName(48)).toBe('C3'))
  it('maps 49 → C#3',          () => expect(noteName(49)).toBe('C#3'))
  it('maps 36 → C2',           () => expect(noteName(36)).toBe('C2'))
  it('maps 0  → C-1',          () => expect(noteName(0)).toBe('C-1'))
  it('maps 127 → G9',          () => expect(noteName(127)).toBe('G9'))
  it('maps 61 → C#4',          () => expect(noteName(61)).toBe('C#4'))
  it('maps 69 → A4',           () => expect(noteName(69)).toBe('A4'))
})
