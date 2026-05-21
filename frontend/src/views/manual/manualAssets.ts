/**
 * 操作説明 Markdown・画像（views/manual/docs, views/manual/images）
 * Vite の glob でバンドルし、public 配下の fetch に依存しない
 */

const markdownModules = import.meta.glob<string>('./docs/**/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

const imageModules = import.meta.glob<string>(
  [
    './docs/**/images/**/*.{png,jpg,jpeg,gif,webp,svg}',
    './images/**/*.{png,jpg,jpeg,gif,webp,svg}',
  ],
  { query: '?url', import: 'default', eager: true },
)

function normalizePath(p: string): string {
  return p.replace(/\\/g, '/')
}

function buildImageLookup(): Map<string, string> {
  const map = new Map<string, string>()
  for (const [key, url] of Object.entries(imageModules)) {
    const norm = normalizePath(key)
    const m = norm.match(/\/images\/(.+)$/i)
    if (!m) continue
    const rel = `images/${m[1]}`
    map.set(rel, url)
    map.set(`./${rel}`, url)
  }
  return map
}

const imageLookup = buildImageLookup()

function findMarkdownKey(docPath: string): string | undefined {
  const normalized = docPath.replace(/^\//, '').replace(/^\.\//, '')
  return Object.keys(markdownModules).find((key) => {
    const k = normalizePath(key)
    return k.endsWith(`/${normalized}`) || k === `./docs/${normalized}`
  })
}

/** docs/ 直下の相対パスで MD を取得（例: forming-instruction_ja.md） */
export function getManualMarkdown(docPath: string): string | undefined {
  const key = findMarkdownKey(docPath)
  return key ? markdownModules[key] : undefined
}

/** docs 直下ファイル名のみ（ppb_manual_ja.md 等） */
export function getStandaloneManualMarkdown(filename: string): string | undefined {
  return getManualMarkdown(filename)
}

/** ./images/... および ](/images/... を Vite 解決 URL に置換 */
export function normalizeManualMarkdown(mdText: string): string {
  let out = mdText
  out = out.replace(/\.\/images\/([^\s")\]]+)/g, (matched, sub) => {
    const url = imageLookup.get(`images/${sub}`)
    return url ?? matched
  })
  out = out.replace(/\]\(\/images\/([^)]+)\)/g, (_, sub) => {
    const url = imageLookup.get(`images/${sub}`)
    return url ? `](${url})` : `](/images/${sub})`
  })
  return out
}
