# マニュアル（views/manual）

操作説明の **Vue 画面**・**Markdown**・**PDF**・**スクリーンショット** をこのフォルダで管理します。

画面単位の操作説明（`pageOperation`）は **PDF 正本**（`pdfs/`）。体裁・生成手順はリポジトリ直下
`.cursor/rules/page-operation-pdf-manual.mdc` および `docs/README`（本フォルダ内 `docs/README.md`）に従う。

```
manual/
├── ManualHome.vue        … マニュアルホーム（左一覧・右本文）
├── ManualViewer.vue      … 単体 Markdown ビューア（レガシー）
├── manualAssets.ts       … MD / 画像の Vite glob 読み込み
├── docs/                 … 操作説明 Markdown（正本は直下のみ）
│   ├── README.md
│   ├── forming-instruction_ja.md
│   ├── cutting-instruction_ja.md
│   ├── plan-baseline_ja.md   … 旧稿（正本は pdfs/plan-baseline.pdf）
│   ├── inspection-actual_ja.md
│   ├── inspection-actual-android_ja.md
│   ├── inspection-actual-registration_ja.md
│   └── inspection-monitor_ja.md
│   └── inspection-productivity_ja.md
└── images/               … スクリーンショット
    ├── FormingInstructionManual/  … forming-instruction_ja.md 用
    ├── InspectionActualDataCollection/
    ├── InspectionActualAndroid/
    ├── InspectionActualRegistration/
    ├── InspectionMonitor/
    ├── InspectionProductivity/
    └── ProductionPlanBaselineManagement/
```

画像パスは Markdown 内で `./images/サブフォルダ/ファイル.png` を使用してください。
