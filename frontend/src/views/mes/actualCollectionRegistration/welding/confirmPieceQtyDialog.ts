import { ElMessageBox } from 'element-plus'
import { h, type VNode } from 'vue'

export const WELDING_PIECE_QTY_CONFIRM_CLASS = 'iar-qty-confirm-box'

export interface WeldingPieceQtyConfirmOptions {
  pieceQty: number
  productName?: string
  productCd?: string
  isEdit?: boolean
}

function formatPieceQty(n: number): string {
  return Math.max(0, Math.round(n)).toLocaleString('ja-JP')
}

export function buildWeldingPieceQtyConfirmMessage(options: WeldingPieceQtyConfirmOptions): VNode {
  const productLabel = (options.productName || options.productCd || '').trim()
  const productCd = (options.productCd || '').trim()
  const showCd = Boolean(productCd && productCd !== productLabel)

  return h('div', { class: 'iar-qty-confirm' }, [
    h('p', { class: 'iar-qty-confirm__lead' }, '入力した本数で登録します。内容をご確認ください。'),
    h('div', { class: 'iar-qty-confirm__card' }, [
      h('div', { class: 'iar-qty-confirm__card-head' }, [
        h('span', { class: 'iar-qty-confirm__badge' }, '生産数'),
      ]),
      h('div', { class: 'iar-qty-confirm__value-row' }, [
        h('span', { class: 'iar-qty-confirm__value' }, formatPieceQty(options.pieceQty)),
        h('span', { class: 'iar-qty-confirm__unit' }, '本'),
      ]),
      productLabel
        ? h('div', { class: 'iar-qty-confirm__product' }, [
            h('span', { class: 'iar-qty-confirm__product-label' }, '製品'),
            h('span', { class: 'iar-qty-confirm__product-name' }, productLabel),
            showCd ? h('span', { class: 'iar-qty-confirm__product-cd' }, productCd) : null,
          ])
        : null,
    ]),
    h(
      'p',
      { class: 'iar-qty-confirm__question' },
      options.isEdit ? 'この内容で更新しますか？' : 'この内容で登録しますか？',
    ),
  ])
}

export async function confirmWeldingPieceQty(options: WeldingPieceQtyConfirmOptions): Promise<void> {
  await ElMessageBox.confirm(buildWeldingPieceQtyConfirmMessage(options), '生産数の確認', {
    confirmButtonText: options.isEdit ? '更新する' : '登録する',
    cancelButtonText: '戻る',
    customClass: WELDING_PIECE_QTY_CONFIRM_CLASS,
    distinguishCancelAndClose: true,
    autofocus: 'confirm',
    center: false,
  })
}
