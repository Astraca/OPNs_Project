import { Empty } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { ClassificationMetricItem } from "../../types/model";
import EChartView from "./EChartView";


const METRIC_COLORS: Record<string, string> = {
  accuracy: "#3b82f6",
  precision: "#16a34a",
  recall: "#d97706",
  f1: "#dc2626",
};

type Props = {
  metrics: ClassificationMetricItem[];
};

export default function ModelMetricsBarChart({ metrics }: Props) {
  const option = useMemo<EChartsOption>(() => {
    const targets = metrics.map((m) => m.target_name);
    const metricKeys = ["accuracy", "precision", "recall", "f1"] as const;

    // Compute dynamic y-axis range to make small differences visible
    const allValues = metrics.flatMap((m) =>
      metricKeys.map((k) => m[k]).filter((v): v is number => typeof v === "number"),
    );
    const dataMin = allValues.length > 0 ? Math.min(...allValues) : 0;
    const dataMax = allValues.length > 0 ? Math.max(...allValues) : 1;
    const padding = Math.max((dataMax - dataMin) * 0.15, 0.02);
    const yMin = Math.max(0, dataMin - padding);
    const yMax = Math.min(1, dataMax + padding);

    return {
      tooltip: {
        trigger: "axis",
        valueFormatter: (value) =>
          typeof value === "number" ? value.toFixed(4) : String(value),
      },
      legend: {
        data: metricKeys.map((k) => k.charAt(0).toUpperCase() + k.slice(1)),
        bottom: 0,
      },
      grid: { left: 48, right: 24, top: 28, bottom: 44 },
      xAxis: {
        type: "category",
        data: targets,
        axisLabel: { rotate: targets.length > 4 ? 30 : 0 },
      },
      yAxis: {
        type: "value",
        name: "分数",
        min: yMin,
        max: yMax,
      },
      series: metricKeys.map((key) => ({
        name: key.charAt(0).toUpperCase() + key.slice(1),
        type: "bar",
        data: metrics.map((m) => m[key]),
        itemStyle: { color: METRIC_COLORS[key] },
        barGap: "10%",
      })),
    };
  }, [metrics]);

  if (!metrics.length) {
    return <Empty description="暂无指标数据" />;
  }

  return <EChartView option={option} height={360} />;
}
