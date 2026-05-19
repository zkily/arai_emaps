import MarkdownIt from 'markdown-it'

/** GitHub 風見出しアンカー（操作説明 MD の目次リンクと一致） */
export function slugifyHeading(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/<[^>]*>/g, '')
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
}

export function createHelpMarkdownIt(): MarkdownIt {
  const md = new MarkdownIt({
    html: true,
    linkify: true,
    breaks: true,
    typographer: true,
  })

  const defaultHeadingOpen =
    md.renderer.rules.heading_open ||
    ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options))

  md.renderer.rules.heading_open = (tokens, idx, options, env, self) => {
    const inline = tokens[idx + 1]
    if (inline?.type === 'inline' && inline.content) {
      const id = slugifyHeading(inline.content)
      if (id) tokens[idx].attrSet('id', id)
    }
    return defaultHeadingOpen(tokens, idx, options, env, self)
  }

  return md
}

export function renderHelpMarkdown(mdText: string): string {
  const normalized = mdText.replace(/\.\/images\//g, '/images/')
  return createHelpMarkdownIt().render(normalized)
}

/** 目次・本文の # アンカーを確実にスクロール（SPA 内でも動作） */
export function bindHelpContentAnchorNav(container: HTMLElement | null): () => void {
  if (!container) return () => {}

  const onClick = (e: MouseEvent) => {
    const anchor = (e.target as HTMLElement | null)?.closest(
      'a[href^="#"]',
    ) as HTMLAnchorElement | null
    if (!anchor || !container.contains(anchor)) return

    const raw = anchor.getAttribute('href')
    if (!raw || raw === '#') return

    const id = decodeURIComponent(raw.slice(1))
    const el = document.getElementById(id)
    if (!el) return

    e.preventDefault()
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    history.replaceState(null, '', `#${encodeURIComponent(id)}`)
  }

  container.addEventListener('click', onClick)
  return () => container.removeEventListener('click', onClick)
}

export function scrollHelpToHash(): void {
  const hash = decodeURIComponent(window.location.hash.slice(1))
  if (!hash) return
  document.getElementById(hash)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
