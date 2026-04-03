<template>
  <div class="pma-help">
    <header class="pma-help__head">
      <div class="pma-help__head-main">
        <el-icon class="pma-help__head-icon" :size="28"><Reading /></el-icon>
        <div>
          <h1 class="pma-help__h1">製品材料照会</h1>
          <p class="pma-help__sub">操作説明（詳細版）</p>
        </div>
      </div>
      <div class="pma-help__head-actions">
        <el-button size="small" :icon="Back" @click="goBack">照会画面へ戻る</el-button>
        <el-button size="small" type="primary" plain :icon="Printer" @click="doPrint">この説明を印刷</el-button>
      </div>
    </header>

    <main class="pma-help__main">
      <!-- 図1: 目的・全体像 -->
      <section class="pma-help__section">
        <h2 class="pma-help__h2"><span class="pma-help__num">1</span> 画面の目的</h2>
        <p class="pma-help__p">
          <strong>製品材料照会</strong>は、<strong>看板発行（<code>kanban_issuance</code>）</strong>を起点に、どの製品がどの原材料・どのロット系統で追跡できるかを一覧で確認する画面です。品質・トレーサビリティ確認に使います。
        </p>
        <figure class="pma-help__figure">
          <figcaption class="pma-help__cap">図1　データのつながり（概念図）</figcaption>
          <svg class="pma-help__svg" viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <defs>
              <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#e0f2fe" />
                <stop offset="100%" style="stop-color:#bae6fd" />
              </linearGradient>
              <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#fef3c7" />
                <stop offset="100%" style="stop-color:#fde68a" />
              </linearGradient>
              <linearGradient id="g3" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#d1fae5" />
                <stop offset="100%" style="stop-color:#a7f3d0" />
              </linearGradient>
              <marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                <polygon points="0 0, 8 4, 0 8" fill="#334155" />
              </marker>
            </defs>
            <rect x="8" y="60" width="200" height="88" rx="10" fill="url(#g1)" stroke="#0284c7" stroke-width="1.5" />
            <text x="108" y="100" text-anchor="middle" font-size="13" font-weight="700" fill="#0c4a6e">看板発行</text>
            <text x="108" y="122" text-anchor="middle" font-size="11" fill="#075985">kanban_issuance</text>
            <path d="M 208 104 L 248 104" stroke="#334155" stroke-width="2" marker-end="url(#arr)" />
            <rect x="252" y="60" width="200" height="88" rx="10" fill="url(#g2)" stroke="#d97706" stroke-width="1.5" />
            <text x="352" y="96" text-anchor="middle" font-size="13" font-weight="700" fill="#78350f">材料使用ログ</text>
            <text x="352" y="118" text-anchor="middle" font-size="11" fill="#92400e">material_cutting_logs</text>
            <text x="352" y="136" text-anchor="middle" font-size="10" fill="#57534e">管理コードで突合</text>
            <path d="M 452 104 L 492 104" stroke="#334155" stroke-width="2" />
            <rect x="496" y="60" width="216" height="88" rx="10" fill="url(#g3)" stroke="#059669" stroke-width="1.5" />
            <text x="604" y="96" text-anchor="middle" font-size="13" font-weight="700" fill="#064e3b">材料受入ログ</text>
            <text x="604" y="118" text-anchor="middle" font-size="11" fill="#047857">material_logs</text>
            <text x="604" y="136" text-anchor="middle" font-size="10" fill="#57534e">製造番号で突合</text>
            <text x="360" y="28" text-anchor="middle" font-size="12" font-weight="600" fill="#1e293b">本画面の一覧行 ＝ 看板1行 ＋ 突合で付与した切断・受入情報</text>
          </svg>
        </figure>
      </section>

      <!-- 図2: 画面構成 -->
      <section class="pma-help__section">
        <h2 class="pma-help__h2"><span class="pma-help__num">2</span> 画面の構成</h2>
        <ol class="pma-help__ol">
          <li><strong>上部バー</strong>：件数表示、<strong>印刷</strong>（現在の検索条件で全件取得して印刷）、<strong>再読込</strong>。</li>
          <li><strong>検索エリア</strong>：キーワード、製品、切断開始日付の期間、検索／クリア。</li>
          <li><strong>一覧テーブル</strong>：製品情報・材料情報・看板情報・突合結果を列で表示。</li>
          <li><strong>ページネーション</strong>：ページサイズ変更時は1ページ目から再検索。</li>
        </ol>
        <figure class="pma-help__figure">
          <figcaption class="pma-help__cap">図2　画面レイアウト（イメージ）</figcaption>
          <svg class="pma-help__svg" viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="8" width="620" height="36" rx="6" fill="#f8fafc" stroke="#cbd5e1" />
            <text x="24" y="30" font-size="12" font-weight="700" fill="#0f172a">製品材料照会　｜　件数　｜　[印刷] [再読込]</text>
            <rect x="10" y="52" width="620" height="40" rx="6" fill="#fff" stroke="#94a3b8" stroke-dasharray="4 3" />
            <text x="24" y="76" font-size="11" fill="#475569">[キーワード] [製品▼] [切断開始 日付範囲] [検索] [クリア]</text>
            <rect x="10" y="100" width="620" height="100" rx="6" fill="#f1f5f9" stroke="#64748b" />
            <text x="320" y="125" text-anchor="middle" font-size="11" font-weight="600" fill="#334155">一覧テーブル（製品CD／原材料／管理コード／材料製造番号／切断開始…）</text>
            <line x1="20" y1="135" x2="620" y2="135" stroke="#cbd5e1" />
            <line x1="20" y1="155" x2="620" y2="155" stroke="#e2e8f0" />
            <line x1="20" y1="175" x2="620" y2="175" stroke="#e2e8f0" />
            <rect x="10" y="206" width="620" height="14" rx="4" fill="#e2e8f0" />
            <text x="320" y="216" text-anchor="middle" font-size="10" fill="#64748b">ページネーション</text>
          </svg>
        </figure>
      </section>

      <!-- 検索条件 -->
      <section class="pma-help__section">
        <h2 class="pma-help__h2"><span class="pma-help__num">3</span> 検索条件の詳細</h2>
        <table class="pma-help__table">
          <thead>
            <tr>
              <th>項目</th>
              <th>内容</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>キーワード</td>
              <td>製品CD・製品名・材料名・管理コード・看板No のいずれかに部分一致（あいまい検索）。Enter でも検索できます。</td>
            </tr>
            <tr>
              <td>製品</td>
              <td>ドロップダウンは、看板データ上の製品CD一覧から生成されます。選択すると即検索（1ページ目）。</td>
            </tr>
            <tr>
              <td>切断開始（日付範囲）</td>
              <td>
                <strong>材料使用ログ</strong>（<code>material_cutting_logs.log_date</code>）の日付で絞り込みます。一覧の「切断開始日」と同じ基準です。該当する切断ログが無い行は、この条件ではヒットしません。
              </td>
            </tr>
            <tr>
              <td>クリア</td>
              <td>キーワード・製品・日付範囲を空にし、1ページ目から再検索します。</td>
            </tr>
          </tbody>
        </table>
        <figure class="pma-help__figure">
          <figcaption class="pma-help__cap">図3　切断開始日付フィルタのイメージ</figcaption>
          <svg class="pma-help__svg pma-help__svg--narrow" viewBox="0 0 520 120" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="40" width="200" height="36" rx="4" fill="#fff" stroke="#0ea5e9" stroke-width="2" />
            <text x="120" y="62" text-anchor="middle" font-size="11" fill="#0369a1">2026/04/01 ～ 2026/04/30</text>
            <text x="120" y="28" text-anchor="middle" font-size="11" font-weight="600" fill="#0f172a">画面上の日付範囲</text>
            <path d="M 230 58 L 270 58" stroke="#64748b" stroke-width="2" marker-end="url(#a2)" />
            <defs>
              <marker id="a2" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><polygon points="0 0,7 3.5,0 7" fill="#64748b" /></marker>
            </defs>
            <rect x="280" y="32" width="220" height="52" rx="6" fill="#ecfdf5" stroke="#059669" />
            <text x="390" y="55" text-anchor="middle" font-size="10" fill="#065f46">SQL: cutting_logs の log_date</text>
            <text x="390" y="72" text-anchor="middle" font-size="10" fill="#065f46">が範囲内の行だけ残る</text>
          </svg>
        </figure>
      </section>

      <!-- 列の意味 -->
      <section class="pma-help__section">
        <h2 class="pma-help__h2"><span class="pma-help__num">4</span> 主な列の意味（突合ルール）</h2>
        <ul class="pma-help__ul">
          <li>
            <strong>管理コード</strong>：看板（<code>kanban_issuance.management_code</code>）の値です。
          </li>
          <li>
            <strong>材料製造番号</strong>：<code>material_cutting_logs</code> を管理コードで突合し、<strong>日付・時刻・ID が最新の1件</strong>の <code>manufacture_no</code> を表示します（トリガーで材料コードから算出された値）。
          </li>
          <li>
            <strong>切断開始日／切断開始時刻</strong>：同じく最新1件の切断ログの <code>log_date</code> / <code>log_time</code> です。
          </li>
          <li>
            <strong>材料製造日／仕入先</strong>：<code>material_logs</code> を <code>manufacture_no</code> で突合し、受入ログ側も<strong>最新1件</strong>から <code>manufacture_date</code> と <code>supplier</code> を表示します。
          </li>
          <li>
            <strong>看板発行日</strong>：<code>issue_date</code>。システムでは<strong>2026/04/01 未満の発行日の行は一覧に出ません</strong>（既定フィルタ）。
          </li>
        </ul>
        <figure class="pma-help__figure">
          <figcaption class="pma-help__cap">図4　管理コード → 切断ログ → 受入ログ（同一管理コードの最新切断行を経由）</figcaption>
          <svg class="pma-help__svg" viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="40" width="120" height="70" rx="8" fill="#e0f2fe" stroke="#0284c7" />
            <text x="80" y="72" text-anchor="middle" font-size="11" font-weight="700" fill="#0c4a6e">看板行</text>
            <text x="80" y="92" text-anchor="middle" font-size="10" fill="#0369a1">management_code</text>
            <text x="170" y="78" font-size="18" fill="#334155">→</text>
            <rect x="200" y="40" width="160" height="70" rx="8" fill="#fef9c3" stroke="#ca8a04" />
            <text x="280" y="68" text-anchor="middle" font-size="11" font-weight="700" fill="#713f12">切断ログ</text>
            <text x="280" y="88" text-anchor="middle" font-size="9" fill="#854d0e">同コードで最新1件</text>
            <text x="380" y="78" font-size="18" fill="#334155">→</text>
            <rect x="410" y="40" width="210" height="70" rx="8" fill="#d1fae5" stroke="#059669" />
            <text x="515" y="68" text-anchor="middle" font-size="11" font-weight="700" fill="#064e3b">受入ログ</text>
            <text x="515" y="88" text-anchor="middle" font-size="9" fill="#047857">manufacture_no 一致で最新1件</text>
            <text x="320" y="28" text-anchor="middle" font-size="11" fill="#475569">突合できない列は空欄のまま表示されます</text>
          </svg>
        </figure>
      </section>

      <!-- 並び順・ページ -->
      <section class="pma-help__section">
        <h2 class="pma-help__h2"><span class="pma-help__num">5</span> 並び順・ページング・印刷</h2>
        <ul class="pma-help__ul">
          <li>
            <strong>既定の並び</strong>：<strong>切断開始日 昇順 → 切断開始時刻 昇順</strong>（値が無い行は後ろに回る動きになります）。同じ条件なら看板IDで安定化。
          </li>
          <li>
            <strong>ページサイズ</strong>：既定 20 件。変更すると1ページ目から再読込します。
          </li>
          <li>
            <strong>印刷</strong>：画面上の検索条件のまま、サーバから最大 20,000 件まで取得し、<strong>A4 横</strong>向きで印刷用ウィンドウを開きます。2万件超の場合は先頭 2 万件のみと警告が出ます。
          </li>
        </ul>
      </section>

      <!-- 前提・トラブル -->
      <section class="pma-help__section pma-help__section--note">
        <h2 class="pma-help__h2"><span class="pma-help__num">6</span> 前提・よくある状況</h2>
        <ul class="pma-help__ul">
          <li><strong>材料使用取込</strong>（旧：切断CSV取込）で <code>material_cutting_logs</code> が更新されていること。未取込だと切断系の列が空になります。</li>
          <li><strong>製造番号列</strong>は DB トリガーで埋まります。マイグレーション（<code>213_material_cutting_logs_manufacture_no.sql</code> 等）未適用だとエラーになる場合があります。</li>
          <li>受入ログとの <code>manufacture_no</code> の書式が一致しないと、材料製造日・仕入先が空のままになります。</li>
          <li>権限は他の品質・材料画面と同様、ログイン済みユーザーが利用できます。</li>
        </ul>
      </section>
    </main>

    <footer class="pma-help__foot">
      <p>最終更新：操作説明はアプリ実装に準拠しています。仕様変更時は本ページもあわせて確認してください。</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Back, Printer, Reading } from '@element-plus/icons-vue'

const router = useRouter()

function goBack() {
  router.push({ path: '/erp/quality/material-association/product-material' })
}

function doPrint() {
  window.print()
}
</script>

<style scoped>
.pma-help {
  min-height: 100%;
  padding: 12px 14px 24px;
  background: linear-gradient(165deg, #f8fafc 0%, #f1f5f9 45%, #e2e8f0 100%);
  box-sizing: border-box;
}

.pma-help__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  margin-bottom: 14px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
}

.pma-help__head-main {
  display: flex;
  align-items: center;
  gap: 14px;
}

.pma-help__head-icon {
  color: #0ea5e9;
  flex-shrink: 0;
}

.pma-help__h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.04em;
}

.pma-help__sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: #64748b;
}

.pma-help__head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pma-help__main {
  max-width: 920px;
  margin: 0 auto;
}

.pma-help__section {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 18px 20px 20px;
  margin-bottom: 14px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
}

.pma-help__section--note {
  background: linear-gradient(180deg, #fffbeb 0%, #fff 40%);
  border-color: #fde68a;
}

.pma-help__h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  border-bottom: 2px solid #e0f2fe;
  padding-bottom: 8px;
}

.pma-help__num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: linear-gradient(145deg, #38bdf8, #0ea5e9);
  color: #fff;
  font-size: 13px;
  font-weight: 800;
}

.pma-help__p {
  margin: 0 0 12px;
  font-size: 14px;
  line-height: 1.75;
  color: #334155;
}

.pma-help__p code,
.pma-help__ul code,
.pma-help__table code {
  font-size: 12px;
  padding: 1px 6px;
  background: #f1f5f9;
  border-radius: 4px;
  color: #0f172a;
}

.pma-help__ol,
.pma-help__ul {
  margin: 0 0 12px;
  padding-left: 1.35em;
  font-size: 14px;
  line-height: 1.8;
  color: #334155;
}

.pma-help__ol li,
.pma-help__ul li {
  margin-bottom: 6px;
}

.pma-help__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-bottom: 14px;
}

.pma-help__table th,
.pma-help__table td {
  border: 1px solid #cbd5e1;
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}

.pma-help__table th {
  background: #f8fafc;
  font-weight: 700;
  color: #1e293b;
  width: 22%;
}

.pma-help__figure {
  margin: 16px 0 0;
  padding: 12px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px dashed #cbd5e1;
}

.pma-help__cap {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.pma-help__svg {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
}

.pma-help__svg--narrow {
  max-width: 520px;
  margin: 0 auto;
}

.pma-help__foot {
  max-width: 920px;
  margin: 18px auto 0;
  padding: 12px 16px;
  font-size: 12px;
  color: #64748b;
  text-align: center;
}

@media print {
  .pma-help__head-actions {
    display: none;
  }
  .pma-help {
    background: #fff;
    padding: 8px;
  }
  .pma-help__section {
    break-inside: avoid;
    box-shadow: none;
  }
}
</style>
