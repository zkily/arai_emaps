import type { LocaleType } from '@/i18n'

const BCP47: Record<LocaleType, string> = {
  zh: 'zh-CN',
  ja: 'ja-JP',
  en: 'en-US',
  vi: 'vi-VN',
}

/** 整数千位分隔（与界面语言一致） */
export function formatInteger(value: number, locale: LocaleType): string {
  return Number(value).toLocaleString(BCP47[locale] ?? 'ja-JP')
}

/** 金额/数量等小数位可控的本地化数字（不含货币符号） */
export function formatDecimal(
  value: number,
  locale: LocaleType,
  fractionDigits = 0,
): string {
  return Number(value).toLocaleString(BCP47[locale] ?? 'ja-JP', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}
