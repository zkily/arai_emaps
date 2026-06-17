const AVATAR_PALETTES: [string, string][] = [
  ['#667eea', '#764ba2'],
  ['#10b981', '#059669'],
  ['#f59e0b', '#d97706'],
  ['#3b82f6', '#2563eb'],
  ['#ec4899', '#db2777'],
]

export function avatarGradientFor(name?: string | null): string {
  const seed = (name ?? '').trim()
  const hash = [...seed].reduce((acc, ch) => acc + ch.charCodeAt(0), 0)
  const idx = Math.abs(hash) % AVATAR_PALETTES.length
  const [start, end] = AVATAR_PALETTES[idx]
  return `linear-gradient(135deg, ${start}, ${end})`
}

export function avatarLetterFor(name?: string | null): string {
  const ch = (name ?? '').trim().charAt(0)
  return ch ? ch.toUpperCase() : '?'
}
