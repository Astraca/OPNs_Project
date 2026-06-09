import { Empty } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { ResidualsData } from "../../types/model";
import EChartView from "./EChartView";


type Props = {
  data: ResidualsData;
};

export default function ResidualsChart({ data }: Props) {
  const option = useMemo<EChartsOption>(
    () => ({
      tooltip: {
        trigger: "item",
        formatter: (params: unknown) => {
          const value = Array.isArray((params as { value?: unknown })?.value)
            ? (params as { value: number[] }).value
            : [];
          return `预测值：${value[0]?.toFixed(4) ?? "-"}<br/>残差：${value[1]?.toFixed(4) ?? "-"}`;
        },
      },
      grid: { left: 56, right: 24, top: 36, bottom: 56 },
      xAxis: { type: "value", name: "预测值" },
      yAxis: { type: "value", name: "残差" },
      series: [
        {
          type: "scatter",
          data: data.predicted.map((pred, i) => [pred, data.residuals[i]]),
          symbolSize: 8,
        },
        {
          type: "line",
          data: (() => {
            const minX = Math.min(...data.predicted);
            const maxX = Math.max(...data.predicted);
            return [[minX, 0], [maxX, 0]];
          })(),
          lineStyle: { type: "dashed", color: "#ccc" },
          silent: true,
        },
      ],
    }),
    [data],
  );

  if (!data.residuals.length) {
    return <Empty description="暂无残差数据" />;
  }

  return <EChartView option={option} height={400} />;
}
