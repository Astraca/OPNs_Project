import { Empty } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { CorrelationMatrixData } from "../../types/dataset";
import EChartView from "./EChartView";


type CorrelationHeatmapProps = {
  data: CorrelationMatrixData;
};

export default function CorrelationHeatmap({ data }: CorrelationHeatmapProps) {
  const values = data.matrix.flat().filter((value): value is number => typeof value === "number");

  const option = useMemo<EChartsOption>(() => {
    const heatmapData = data.matrix.flatMap((row, rowIndex) =>
      row.map((value, columnIndex) => [columnIndex, rowIndex, value]),
    );

    return {
      tooltip: {
        position: "top",
        formatter: (params: unknown) => {
          const item = Array.isArray(params) ? params[0] : params;
          const value = (item as { value?: unknown }).value;
          const coefficient = Array.isArray(value) ? value[2] : "";
          return `相关系数：${coefficient ?? "-"}`;
        },
      },
      grid: { left: 96, right: 32, top: 32, bottom: 92 },
      xAxis: {
        type: "category",
        data: data.columns,
        splitArea: { show: true },
        axisLabel: { rotate: 45 },
      },
      yAxis: {
        type: "category",
        data: data.columns,
        splitArea: { show: true },
      },
      visualMap: {
        min: -1,
        max: 1,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 8,
        inRange: { color: ["#2563eb", "#f8fafc", "#dc2626"] },
      },
      series: [
        {
          type: "heatmap",
          data: heatmapData,
          label: { show: false },
          emphasis: {
            itemStyle: {
              shadowBlur: 8,
              shadowColor: "rgba(15, 23, 42, 0.25)",
            },
          },
        },
      ],
    };
  }, [data.columns, data.matrix]);

  if (data.columns.length < 2 || !values.length) {
    return <Empty description="数值字段不足，无法计算相关性" />;
  }

  return <EChartView option={option} height={420} />;
}
