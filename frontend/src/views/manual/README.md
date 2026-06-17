# マニュアル（views/manual）

操作説明の **Vue 画面**・**Markdown**・**スクリーンショット** をこのフォルダで管理します。

```
manual/
├── ManualHome.vue        … マニュアルホーム（左一覧・右本文）
├── ManualViewer.vue      … 単体 Markdown ビューア（レガシー）
├── manualAssets.ts       … MD / 画像の Vite glob 読み込み
├── docs/                 … 操作説明 Markdown（正本は直下のみ）
│   ├── README.md
│   ├── forming-instruction_ja.md
│   ├── cutting-instruction_ja.md
│   ├── plan-baseline_ja.md
│   ├── inspection-actual_ja.md
│   ├── inspection-actual-registration_ja.md
│   └── inspection-monitor_ja.md
└── images/               … スクリーンショット
    ├── FormingInstructionManual/  … forming-instruction_ja.md 用
    ├── InspectionActualDataCollection/
    ├── InspectionActualRegistration/
    ├── InspectionMonitor/
    └── ProductionPlanBaselineManagement/
```

画像パスは Markdown 内で `./images/サブフォルダ/ファイル.png` を使用してください。
