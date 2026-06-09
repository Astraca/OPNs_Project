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
        min: 0,
        max: 1,
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
