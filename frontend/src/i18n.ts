import { createI18n } from 'vue-i18n'
import en from './locales/en'
import ja from './locales/ja'
import zh from './locales/zh'
import vi from './locales/vi'

export const LOCALE_KEY = 'app-locale'
export type LocaleType = 'en' | 'ja' | 'zh' | 'vi'

const saved = (typeof localStorage !== 'undefined' && localStorage.getItem(LOCALE_KEY)) as LocaleType | null
const fallback: LocaleType = 'ja'
const defaultLocale: LocaleType = (saved && ['en', 'ja', 'zh', 'vi'].includes(saved)) ? saved : fallback

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: defaultLocale,
  fallbackLocale: 'ja',
  messages: {
    en,
    ja,
    zh,
    vi,
  },
})

export function setLocale(locale: LocaleType) {
  i18n.global.locale.value = locale
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(LOCALE_KEY, locale)
  }
}

export function getLocale(): LocaleType {
  return i18n.global.locale.value as LocaleType
}
