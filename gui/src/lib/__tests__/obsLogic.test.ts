import { describe, it, expect } from 'vitest'
import { assignedScenes, nextUnassignedScene } from '../obsLogic.js'
import type { ActionConfig } from '../types.js'

// ── assignedScenes ──────────────────────────────────────────────────────────

describe('assignedScenes', () => {
  it('returns an empty set for an empty config', () => {
    expect(assignedScenes({})).toEqual(new Set())
  })

  it('collects scene names from static actions', () => {
    const entries: Record<string, ActionConfig> = {
      '48': { action: 'static', scene: 'Scene A' },
      '49': { action: 'static', scene: 'Scene B' },
    }
    expect(assignedScenes(entries)).toEqual(new Set(['Scene A', 'Scene B']))
  })

  it('ignores non-static actions', () => {
    const entries: Record<string, ActionConfig> = {
      '48': { action: 'loop', prefix: 'Cam ', style: 'cycle', bpm: 120, steps: 4 },
      '49': { action: 'stop' },
      '50': { action: 'pause' },
      '51': { action: 'sequence', steps: [] },
    }
    expect(assignedScenes(entries)).toEqual(new Set())
  })

  it('handles duplicate scene names (same scene on multiple notes)', () => {
    const entries: Record<string, ActionConfig> = {
      '48': { action: 'static', scene: 'Main' },
      '49': { action: 'static', scene: 'Main' },
    }
    expect(assignedScenes(entries)).toEqual(new Set(['Main']))
  })
})

// ── nextUnassignedScene ─────────────────────────────────────────────────────

describe('nextUnassignedScene', () => {
  it('returns the first scene when none are assigned', () => {
    expect(nextUnassignedScene(['A', 'B', 'C'], {})).toBe('A')
  })

  it('skips already-assigned scenes', () => {
    const entries: Record<string, ActionConfig> = {
      '48': { action: 'static', scene: 'A' },
    }
    expect(nextUnassignedScene(['A', 'B', 'C'], entries)).toBe('B')
  })

  it('skips multiple consecutive assigned scenes', () => {
    const entries: Record<string, ActionConfig> = {
      '48': { action: 'static', scene: 'A' },
      '49': { action: 'static', scene: 'B' },
    }
    expect(nextUnassignedScene(['A', 'B', 'C'], entries)).toBe('C')
  })

  it('returns null when all scenes are assigned', () => {
    const entries: Record<string, ActionConfig> = {
      '48': { action: 'static', scene: 'A' },
      '49': { action: 'static', scene: 'B' },
    }
    expect(nextUnassignedScene(['A', 'B'], entries)).toBeNull()
  })

  it('respects a non-zero startIdx', () => {
    expect(nextUnassignedScene(['A', 'B', 'C'], {}, 1)).toBe('B')
  })

  it('returns null when startIdx is past the end', () => {
    expect(nextUnassignedScene(['A', 'B'], {}, 3)).toBeNull()
  })

  it('returns null for an empty scenes array', () => {
    expect(nextUnassignedScene([], {})).toBeNull()
  })

  it('is not affected by non-static actions', () => {
    const entries: Record<string, ActionConfig> = {
      '48': { action: 'loop', prefix: 'Cam ', style: 'cycle', bpm: 120, steps: 4 },
    }
    // Loop action doesn't "use" scene 'A', so 'A' should be returned
    expect(nextUnassignedScene(['A', 'B'], entries)).toBe('A')
  })
})
