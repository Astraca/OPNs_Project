import { BarChart, HeatmapChart, LineChart, ScatterChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent, VisualMapComponent } from "echarts/components";
import * as echarts from "echarts/core";
import type { EChartsOption } from "echarts";
import { CanvasRenderer } from "echarts/renderers";
import { useEffect, useRef } from "react";

import "./Charts.css";


echarts.use([
  BarChart,
  HeatmapChart,
  LineChart,
  ScatterChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
]);


type EChartViewProps = {
  option: EChartsOption;
  height?: number;
};

export default function EChartView({ option, height = 320 }: EChartViewProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chartRef.current) {
      return undefined;
    }

    const chart = echarts.init(chartRef.current);
    chart.setOption(option, true);

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [option]);

  return <div className="chart-view" ref={chartRef} style={{ height }} />;
}
