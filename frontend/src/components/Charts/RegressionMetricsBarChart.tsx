import { Empty } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { RegressionMetricItem } from "../../types/model";
import EChartView from "./EChartView";


const METRIC_CONFIG: { key: keyof RegressionMetricItem; label: string; color: string; skipZero?: boolean }[] = [
  { key: "mae", label: "MAE", color: "#3b82f6" },
  { key: "rmse", label: "RMSE", color: "#dc2626" },
  { key: "r2", label: "R²", color: "#16a34a" },
];

type Props = {
  metrics: RegressionMetricItem | null;
};

export default function RegressionMetricsBarChart({ metrics }: Props) {
  const option = useMemo<EChartsOption>(() => {
    if (!metrics) return {};

    const bars = METRIC_CONFIG.filter((cfg) => metrics[cfg.key] != null).map((cfg) => ({
      name: cfg.label,
      value: metrics[cfg.key] as number,
      color: cfg.color,
    }));

    return {
      tooltip: {
        trigger: "axis",
        valueFormatter: (value) =>
          typeof value === "number" ? value.toFixed(4) : String(value),
      },
      grid: { left: 60, right: 32, top: 28, bottom: 48 },
      xAxis: {
        type: "category",
        data: bars.map((b) => b.name),
      },
      yAxis: {
        type: "value",
        name: "值",
      },
      series: [
        {
          type: "bar",
          data: bars.map((b) => ({
            value: b.value,
            itemStyle: { color: b.color, borderRadius: [4, 4, 0, 0] },
          })),
          barWidth: "50%",
          label: {
            show: true,
            position: "top",
            formatter: (params: unknown) => {
              const v = (params as { value?: number }).value;
              return v != null ? v.toFixed(4) : "";
            },
          },
        },
      ],
    };
  }, [metrics]);

  if (!metrics) {
    return <Empty description="暂无回归指标" />;
  }

  return <EChartView option={option} height={320} />;
}
