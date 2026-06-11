/** menu.<CODE> i18n を優先し、未定義時は menuConfig の name にフォールバック（SidebarMenu と同じ） */
export function resolveMenuLabel(
  code: string,
  fallbackName: string,
  translate: (key: string) => string,
): string {
  const key = `menu.${code}`
  const translated = translate(key)
  return translated === key ? fallbackName : translated
}
