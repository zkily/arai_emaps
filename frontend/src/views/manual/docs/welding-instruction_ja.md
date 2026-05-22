# 溶接工程生産指示及び実績収集マニュアル

| 項目 | 内容 |
|------|------|
| テーマ | 溶接工程における生産指示の発行、現場実績収集、ERP／APS への反映 |
| 主な対象画面 | 溶接指示、生産実績管理、生産データ管理、溶接計画一覧、溶接計画作成 |

本書は、溶接工程の **日次運用フロー** を、メニュー操作・現場作業・データ照合・計画修正まで一通り説明します。

---

## 目次

1. [業務フロー概要](#1-業務フロー概要)
2. [溶接指示書の発行（指示書発行）](#2-溶接指示書の発行指示書発行)
3. [現場での指示書交換](#3-現場での指示書交換)
4. [ハンディターミナルによる実績登録](#4-ハンディターミナルによる実績登録)
5. [実績照合（生産実績管理）](#5-実績照合生産実績管理)
6. [収集実績のデータベース更新（全部一括更新）](#6-収集実績のデータベース更新全部一括更新)
7. [データベース調整（在庫 TAB）](#7-データベース調整在庫-tab)
8. [APS 再計算と生産残の修正](#8-aps-再計算と生産残の修正)
9. [段取予定表印刷と現場掲示](#9-段取予定表印刷と現場掲示)
10. [推奨スクリーンショット一覧](#10-推奨スクリーンショット一覧)
11. [よくあるメッセージと対処](#11-よくあるメッセージと対処)

---

## 1. 業務フロー概要

溶接工程の **1 日（1 サイクル）** は、おおむね次の流れで進めます。上から順に実施し、前の工程が終わってから次へ進めてください。

<div class="forming-workflow" role="img" aria-label="溶接工程 業務フロー AからJ">
  <p class="forming-workflow__title">溶接工程指示・実績収集業務フロー（A → J）</p>

  <section class="forming-workflow__lane forming-workflow__lane--office">
    <header class="forming-workflow__lane-hd">計画・事務（ERP）— 指示の準備</header>
    <div class="forming-workflow__steps">
      <div class="forming-workflow__step"><span class="forming-workflow__badge">A</span><span class="forming-workflow__text">溶接生産指示書の発行・印刷</span></div>
    </div>
  </section>

  <div class="forming-workflow__connector" aria-hidden="true">↓</div>

  <section class="forming-workflow__lane forming-workflow__lane--field">
    <header class="forming-workflow__lane-hd">溶接現場 — 実績の収集</header>
    <div class="forming-workflow__steps forming-workflow__steps--row">
      <div class="forming-workflow__step"><span class="forming-workflow__badge">B</span><span class="forming-workflow__text">新規指示書の配布と記入済み指示書の回収</span></div>
      <span class="forming-workflow__arrow" aria-hidden="true">→</span>
      <div class="forming-workflow__step"><span class="forming-workflow__badge">C</span><span class="forming-workflow__text">ハンディターミナル（HT）で実績登録</span></div>
    </div>
  </section>

  <div class="forming-workflow__connector" aria-hidden="true">↓</div>

  <section class="forming-workflow__lane forming-workflow__lane--sync">
    <header class="forming-workflow__lane-hd">事務（ERP）— 照合と反映</header>
    <div class="forming-workflow__steps forming-workflow__steps--row">
      <div class="forming-workflow__step"><span class="forming-workflow__badge">D</span><span class="forming-workflow__text">生産実績管理で HT・指示書と照合</span></div>
      <span class="forming-workflow__arrow" aria-hidden="true">→</span>
      <div class="forming-workflow__step"><span class="forming-workflow__badge">E</span><span class="forming-workflow__text">生産データ管理で全部一括更新</span></div>
      <span class="forming-workflow__arrow" aria-hidden="true">→</span>
      <div class="forming-workflow__step forming-workflow__step--optional"><span class="forming-workflow__badge">F</span><span class="forming-workflow__text">必要な場合のみ在庫 TAB で数量を修正</span></div>
    </div>
  </section>

  <div class="forming-workflow__connector" aria-hidden="true">↓</div>

  <section class="forming-workflow__lane forming-workflow__lane--aps">
    <header class="forming-workflow__lane-hd">計画（APS）— 計画の見直しと掲示</header>
    <div class="forming-workflow__steps forming-workflow__steps--row">
      <div class="forming-workflow__step"><span class="forming-workflow__badge">G</span><span class="forming-workflow__text">溶接計画一覧でライン順に再計算</span></div>
      <span class="forming-workflow__arrow" aria-hidden="true">→</span>
      <div class="forming-workflow__step"><span class="forming-workflow__badge">H</span><span class="forming-workflow__text">生産残を確認し、合計数量などを修正</span></div>
      <span class="forming-workflow__arrow" aria-hidden="true">→</span>
      <div class="forming-workflow__step"><span class="forming-workflow__badge">I</span><span class="forming-workflow__text">もう一度再計算して計画を確定</span></div>
      <span class="forming-workflow__arrow" aria-hidden="true">→</span>
      <div class="forming-workflow__step"><span class="forming-workflow__badge">J</span><span class="forming-workflow__text">段取予定表を印刷し、現場に掲示</span></div>
    </div>
  </section>
</div>

| 段階 | 作業内容 | 主な担当 |
|------|----------|----------|
| 指示発行 | 翌日分の溶接生産指示書を印刷 | 事務／計画 |
| 現場交換 | 新規指示書と記入済み指示書を交換 | 溶接現場 |
| 実績収集 | HT 登録 | 事務／現場 |
| 照合・反映 | ERP で実績確認 → DB 更新 | 事務 |
| 計画修正 | APS 再計算、残数調整、段取予定表掲示 | 事務 |

![業務フロー概要](./images/WeldingInstructionManual/01_workflow_overview.png)

---

## 2. 溶接指示書の発行（指示書発行）

### 2.1 画面へのアクセス

1. Smart-EMAPs にログインします。
2. 左サイドメニューから次の順に開きます。  
   **ERP管理メニュー** → **生産管理** → **生産指示** → **溶接指示**
3. 画面タイトル **「溶接指示書発行管理」** が表示されます。

![メニューから溶接指示を開く](./images/WeldingInstructionManual/02_menu_welding_instruction.png)

### 2.2 画面構成

![溶接指示書発行管理 画面全体](./images/WeldingInstructionManual/03_welding_instruction_overview.png)

| エリア | 説明 |
|--------|------|
| ヘッダー | 計画生産数・稼働設備数のサマリ、「データ更新」ボタン |
| 検索バー | 生産日、設備選択、キーワード検索、各種印刷ボタン |
| 計画テーブル | 生産日・設備名・製品・計画生産数・能率・段取時間・備考 等 |
| チャート | 日別計画・実績生産数 |

### 2.3 「指示書発行」の操作手順

> **重要**：**原則として翌日の生産日** を選んでから発行してください。

1. **生産日を設定する**
   - 検索バーの **「生産日」** で対象日を選択します。
   - ショートカット **「翌日」** ボタンを押すと、翌日の日付が設定されます（推奨）。

   ![生産日を翌日に設定](./images/WeldingInstructionManual/04_welding_date_nextday.png)

2. **必要に応じて絞り込む**（任意）
   - **設備選択**：特定溶接機のみ印刷する場合
   - **製品名・設備名検索**：キーワードで計画一覧を絞り込み

3. **「指示書発行」ボタンをクリックする**
   - ボタン位置：検索バー右側、**緑色** の **「指示書発行」** ボタン

   ![指示書発行ボタン](./images/WeldingInstructionManual/05_instruction_issue_button.png)

4. **印刷処理の流れ**
   - システムが有効な **溶接設備ごとに 1 ページ** の指示書 HTML を生成します。
   - 画面上にプレビューが表示され、**QR コード（製品 CD）の読込** が完了するまで「QRコード読み込み中...」と表示されます。
   - 読込完了後、**ブラウザの印刷ダイアログが自動的に開きます**<span style="color: #dc2626; font-weight: 700;">（A5 横向き）</span>。
   - プレビュー右上の **×** ボタンでキャンセルできます。

   ![指示書印刷プレビュー](./images/WeldingInstructionManual/06_instruction_print_preview.png)

5. **プリンタで印刷する**
   - 各設備分の **「溶接生産指示書」** を印刷します。
   - 印刷後、指示書を溶接現場の各ラインへ配布します。

   ![印刷された溶接生産指示書](./images/WeldingInstructionManual/07_instruction_printed_sample.png)

### 2.4 指示書に含まれる主な情報

- 設備名・設備 CD
- 生産日
- 製品 CD（QR コード付き）
- 生産順位・計画生産数
- 能率・段取時間
- 日別計画一覧

### 2.5 補足操作

| ボタン | 用途 |
|--------|------|
| **データ更新** | 画面上部。計画データを再取得 |
| **前日／今日／翌日** | 生産日のクイック切替 |
| **段取予定発行** | 第 9 章参照。段取予定表を印刷 |

---

## 3. 現場での指示書交換

この工程は **システム画面上の操作ではなく、溶接現場での物理的な手順** です。

### 3.1 目的

- 事務側で新規発行した **翌日分の溶接工程指示書** を現場へ渡す。
- 現場で **記入・実績記録が完了した当日分の指示書** を回収する。

### 3.2 手順

1. 集計担当者が **新規発行した指示書**（第 2 章）を各溶接ラインへ配布する。
2. 現場担当者は、**前日までに使用し記入済みの指示書** を集計担当者へ返却する。
3. 返却時に確認する項目（例）：
   - 生産数の手書き記入が読み取れるか
4. 回収した指示書は、HT 実績と突合するための **現場記録** として保管する。

![現場での指示書交換](./images/WeldingInstructionManual/08_site_exchange.png)

### 3.3 注意事項

- 指示書の交換は **シフト開始前** または **日替わり時** に実施するのが望ましいです。
- 計画変更が当日中に入った場合は、再発行した指示書で **差し替え** ます。

---

## 4. ハンディターミナルによる実績登録

### 4.1 概要

作業担当者は **ハンディターミナル（HT）** を用いて、溶接実績を登録します。

### 4.2 操作手順（画像参照）

端末の起動、ログイン、実績入力、送信操作は、**下記画像** の順に実施してください。

| 操作 | 内容 |
|------|------|
| 起動 | 端末の電源投入・初期画面の表示 |
| ログイン | 担当者でサインイン |
| 実績入力 | 製品・設備・数量の登録 |
| 送信 | 入力内容の確定と送信 |

![ハンディターミナル：起動・ログイン・実績入力・送信](./images/WeldingInstructionManual/09_handy_terminal.png)

### 4.3 実施タイミングと注意

| 項目 | 内容 |
|------|------|
| 実施タイミング | 当日生産締め時 |
| 入力内容 | 製品、設備、数量 |
| 照合前確認 | 指示書の記入内容と数量が大きく乖離していないか |

---

## 5. 実績照合（生産実績管理）

HT 登録データ・現場指示書の記入内容を、ERP 上の在庫取引実績と **照合** します。

### 5.1 画面へのアクセス

1. **ERP管理メニュー** → **生産管理** → **生産実績** → **生産実績管理**
2. 画面タイトル **「生産実績管理」**

![メニューから生産実績管理](./images/WeldingInstructionManual/10_menu_actual_management.png)

### 5.2 照合の手順

1. **検索条件を設定する**
   - **製品名**、**設備**、**生産日**（前日／今日／翌日 クイックボタン可）

2. **工程別フィルタで「溶接」を選択する**
   - 「工程別フィルタ」タブから **溶接** 工程を選びます。

   ![生産実績管理 溶接タブ](./images/WeldingInstructionManual/11_actual_management_filter.png)

3. **取引ログ一覧で照合する**
   - **HT 登録値・指示書記入値** と ERP の **数量** を突合します。
   - 差異がある行は原因を確認（二重登録、未登録、品種違い 等）。

4. **差異の修正**（必要な場合）
   - 行右端 **「編集」**／**「削除」** で修正
   - 修正後 **「再取得」** で最新状態を確認

### 5.3 照合チェックリスト

| # | 確認内容 | OK |
|---|----------|-----|
| 1 | 対象日の溶接実績件数が HT と同程度か | ☐ |
| 2 | 設備名・製品 CD が指示書と一致しているか | ☐ |
| 3 | 数量の合計が指示書の合計と一致するか | ☐ |

---

## 6. 収集実績のデータベース更新（全部一括更新）

照合が完了したら、収集済み実績を **データベース管理集計テーブル** へ反映します。

### 6.1 画面へのアクセス

1. **ERP管理メニュー** → **生産管理** → **生産計画** → **生産データ管理**
2. 画面タイトル **「生産データ管理」**

> 画面上部の **「各種更新機能」** ドロップダウンから一括更新を実行します。

![メニューと生産データ管理](./images/WeldingInstructionManual/13_menu_data_management.png)

### 6.2 「全部一括更新」の操作手順

1. 画面右上 **「各種更新機能」** ボタン（▼付き）をクリックします。
2. ドロップダウンから **「全部一括更新」** を選択します。
3. 確認ダイアログで更新順序を確認し、**「一括更新開始」** をクリックします。
4. 進捗ダイアログで処理完了を待ちます。

![全部一括更新](./images/WeldingInstructionManual/14_all_batch_update.png)

### 6.3 実行タイミングの目安

- 第 5 章の照合・修正が **すべて完了した後** に 1 回実行する。

---

## 7. データベース調整（在庫 TAB）

一括更新後も、在庫数に **微差** がある場合は、生産データ管理画面の **在庫 TAB** から直接修正します。

### 7.1 在庫 TAB を開く

**生産データ管理** 画面の下部タブ列から **「在庫」**（📦 アイコン）をクリックします。

![生産データ管理：下部タブ列の「在庫」位置](./images/WeldingInstructionManual/15_inventory_tab.png)

### 7.2 セルのダブルクリック修正

1. 修正したい **日付行** と **工程列**（例：溶接実績、溶接不良、溶接在庫 等）の交差セルを **ダブルクリック** します。
2. **「在庫取引ログ入力」** ダイアログが開きます。
3. 工程に応じた入力欄に数量を入力し **登録** します。

![在庫 TAB ダブルクリック](./images/WeldingInstructionManual/15_inventory_tab_dblclick.png)

### 7.3 注意事項

- 製品が当該工程ルートに含まれない場合、「製品は工程に属していません」と表示されます。
- 基本情報列のダブルクリックではダイアログは開きません。

---

## 8. APS 再計算と生産残の修正

実績反映後、APS 側の溶接計画を **ライン順に再計算** し、計画と実績の **「残」** を確認・修正します。

### 8.1 溶接計画一覧で再計算

1. **APS管理メニュー** → **生産計画一覧** → **溶接計画一覧**
2. 画面タイトル **「溶接計画一覧」**
3. **期間** と **工程** を指定し、一覧／ガントを表示します。
4. 右上 **「溶接ライン順で再計算」** ボタン（オレンジ色）をクリックします。
5. 確認メッセージを読み、実行を承認します。
6. **再計算進捗** バーで設備ごとの進行を確認します。


![溶接ライン順で再計算ボタン](./images/WeldingInstructionManual/17_replan_button.png)

### 8.2 生産残の確認（要修正判定）

再計算完了後、日別ガントおよび一覧表の **「翌日の計画残数」** を確認します。

| パターン | 判定基準 |
|----------|----------|
| A. 少量残 | **残 &lt; 50 本** 程度でロットが実質生産完了 |
| B. 次品種着手済み | **残 &gt; 0** なのに **次の品種の計画／実績が既に開始** |

![残数確認（ガント／一覧）](./images/WeldingInstructionManual/18_remain_check_gantt.png)

### 8.3 修正方法（溶接計画作成 — 合計(本)）

1. **APS管理メニュー** → **生産計画作成** → **溶接計画作成** を開きます。
2. 対象 **設備（ライン）** の **「合計(本)」** セルを **ダブルクリック** して数量を修正します。
3. 保存後、溶接計画一覧で **再度「溶接ライン順で再計算」** を実行します。

| 項目 | 値 |
|------|-----|
| URL パス | `/aps/welding-planning` |

![合計(本)の編集](./images/WeldingInstructionManual/19_welding_planning_total_qty.png)

---

## 9. 段取予定表印刷と現場掲示

残数修正と **2 回目の APS 再計算**（第 8.3 節末尾）が完了したら、翌日および **翌稼働日** の段替予定を現場へ掲示します。

### 9.1 再度 APS 再計算

1. **溶接計画一覧** で **「溶接ライン順で再計算」** を **もう一度** 実行します（第 8.1 節と同じ）。

### 9.2 溶接指示画面で段取予定表を印刷

1. **ERP管理メニュー** → **生産管理** → **生産指示** → **溶接指示** を開きます。
2. **生産日** を **翌日** に設定します。
3. **「段取予定発行」** ボタンをクリックして印刷します（A4 横向き）。
4. 印刷物タイトル：**「溶接生産計画段替予定表」**

![段取予定発行ボタン](./images/WeldingInstructionManual/20_setup_schedule_print.png)  
![段替予定表（印刷サンプル）](./images/WeldingInstructionManual/21_setup_schedule_sample.png)

### 9.3 現場掲示

1. 印刷した **溶接生産計画段替予定表** を、溶接工程の掲示板に掲出します。
2. 掲示対象：**翌日分** が分かる部分。
3. 古い段替表は **剥がして差し替え** ます。

---

## 10. 推奨スクリーンショット一覧

| 番号 | 画像 | 用途 |
|------|------|------|
| 01 | [01_workflow_overview.png](./images/WeldingInstructionManual/01_workflow_overview.png) | 業務フロー |
| 02 | [02_menu_welding_instruction.png](./images/WeldingInstructionManual/02_menu_welding_instruction.png) | メニュー（溶接指示） |
| 03 | [03_welding_instruction_overview.png](./images/WeldingInstructionManual/03_welding_instruction_overview.png) | 溶接指示画面全体 |
| 04 | [04_welding_date_nextday.png](./images/WeldingInstructionManual/04_welding_date_nextday.png) | 翌日設定 |
| 05 | [05_instruction_issue_button.png](./images/WeldingInstructionManual/05_instruction_issue_button.png) | 指示書発行 |
| 06 | [06_instruction_print_preview.png](./images/WeldingInstructionManual/06_instruction_print_preview.png) | 印刷プレビュー |
| 07 | [07_instruction_printed_sample.png](./images/WeldingInstructionManual/07_instruction_printed_sample.png) | 指示書サンプル |
| 08 | [08_site_exchange.png](./images/WeldingInstructionManual/08_site_exchange.png) | 現場交換 |
| 09 | [09_handy_terminal.png](./images/WeldingInstructionManual/09_handy_terminal.png) | HT 登録 |
| 10 | [10_menu_actual_management.png](./images/WeldingInstructionManual/10_menu_actual_management.png) | メニュー（実績管理） |
| 11 | [11_actual_management_filter.png](./images/WeldingInstructionManual/11_actual_management_filter.png) | 実績照合 |
| 12 | [12_actual_reconcile.png](./images/WeldingInstructionManual/12_actual_reconcile.png) | 照合例 |
| 13 | [13_menu_data_management.png](./images/WeldingInstructionManual/13_menu_data_management.png) | 生産データ管理 |
| 14 | [14_all_batch_update.png](./images/WeldingInstructionManual/14_all_batch_update.png) | 一括更新 |
| 15 | [15_inventory_tab.png](./images/WeldingInstructionManual/15_inventory_tab.png) | 在庫 TAB 位置 |
| — | [15_inventory_tab_dblclick.png](./images/WeldingInstructionManual/15_inventory_tab_dblclick.png) | 在庫セル修正 |
| 16 | [16_menu_welding_plan_list.png](./images/WeldingInstructionManual/16_menu_welding_plan_list.png) | 溶接計画一覧 |
| 17 | [17_replan_button.png](./images/WeldingInstructionManual/17_replan_button.png) | 再計算 |
| 18 | [18_remain_check_gantt.png](./images/WeldingInstructionManual/18_remain_check_gantt.png) | 残確認 |
| 19 | [19_welding_planning_total_qty.png](./images/WeldingInstructionManual/19_welding_planning_total_qty.png) | 合計(本)修正 |
| 20 | [20_setup_schedule_print.png](./images/WeldingInstructionManual/20_setup_schedule_print.png) | 段取予定発行 |
| 21 | [21_setup_schedule_sample.png](./images/WeldingInstructionManual/21_setup_schedule_sample.png) | 段替予定表 |
| 22 | [22_site_posting.png](./images/WeldingInstructionManual/22_site_posting.png) | 現場掲示 |

---

## 11. よくあるメッセージと対処

| メッセージ | 画面 | 対処 |
|------------|------|------|
| 印刷対象の設備がありません | 溶接指示 | 溶接設備マスタ・計画データを確認。データ更新を実行 |
| QRコード読み込み中… | 溶接指示 | ネットワーク確認。完了まで待つか × で中止 |
| 印刷する計画データがありません | 溶接指示（段取予定） | 生産日・APS 計画を確認。再計算後に再試行 |
| 該当データがありません | 生産実績管理 | フィルタ条件（日付・工程・製品）を見直し |
| 他の端末で一括更新が実行中… | 生産データ管理 | 数分待ってから再実行 |
| 合計(本)は 1 以上の整数を入力してください | 溶接計画作成 | 正の整数を入力 |
| 製品は工程に属していません | 生産データ管理 | 製品ルート・工程 CD を確認 |
| 再計算に失敗しました | 溶接計画一覧 | 期間・工程選択を確認。失敗設備名を確認して再実行 |

---

## 改訂履歴

| 日付 | 版 | 内容 |
|------|-----|------|
| 2026-05-21 | 1.0 | 初版作成（溶接工程。成型マニュアルをベースに PLC 手順を除く） |
