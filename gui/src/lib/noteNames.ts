const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] as const

/**
 * Convert a MIDI note number to a human-readable name.
 * Convention: C3 = 48, C4 = 60 (middle C).
 * Examples: noteName(36) → "C2", noteName(49) → "C#3", noteName(60) → "C4"
 */
export function noteName(n: number): string {
  return NOTE_NAMES[n % 12] + (Math.floor(n / 12) - 1)
}
