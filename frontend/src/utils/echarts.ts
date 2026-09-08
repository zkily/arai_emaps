/**
 * ECharts 按需注册入口。业务代码请从此处导入，避免 `import * as echarts from 'echarts'` 全量打包。
 */
import * as echarts from 'echarts/core'
import {
  BarChart,
  GaugeChart,
  LineChart,
  PieChart,
  RadarChart,
  ScatterChart,
} from 'echarts/charts'
import {
  DataZoomComponent,
  DatasetComponent,
  GraphicComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent,
  TitleComponent,
  ToolboxComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components'
import { LabelLayout, UniversalTransition } from 'echarts/features'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  RadarChart,
  ScatterChart,
  GaugeChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  ToolboxComponent,
  MarkPointComponent,
  MarkLineComponent,
  VisualMapComponent,
  DatasetComponent,
  GraphicComponent,
  LabelLayout,
  UniversalTransition,
  CanvasRenderer,
])

export default echarts
export type { ECharts, EChartsOption } from 'echarts'
