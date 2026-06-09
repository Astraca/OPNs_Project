import { Empty } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { PredictedVsActualData } from "../../types/model";
import EChartView from "./EChartView";


type Props = {
  data: PredictedVsActualData;
};

export default function PredictedVsActualChart({ data }: Props) {
  const option = useMemo<EChartsOption>(() => {
    const pairs = data.actual.map((actual, i) => [actual, data.predicted[i]]);
    const allValues = [...data.actual, ...data.predicted];
    const rangeMin = Math.min(...allValues);
    const rangeMax = Math.max(...allValues);
    const padding = (rangeMax - rangeMin) * 0.1 || 1;

    return {
      tooltip: {
        trigger: "item",
        formatter: (params: unknown) => {
          const value = Array.isArray((params as { value?: unknown })?.value)
            ? (params as { value: number[] }).value
            : [];
          return `真实值：${value[0]?.toFixed(4) ?? "-"}<br/>预测值：${value[1]?.toFixed(4) ?? "-"}`;
        },
      },
      grid: { left: 56, right: 24, top: 36, bottom: 56 },
      xAxis: {
        type: "value",
        name: "真实值",
        min: rangeMin - padding,
        max: rangeMax + padding,
      },
      yAxis: {
        type: "value",
        name: "预测值",
        min: rangeMin - padding,
        max: rangeMax + padding,
      },
      series: [
        {
          type: "scatter",
          data: pairs,
          symbolSize: 8,
        },
        {
          type: "line",
          data: [
            [rangeMin - padding, rangeMin - padding],
            [rangeMax + padding, rangeMax + padding],
          ],
          lineStyle: { type: "dashed", color: "#ccc" },
          silent: true,
        },
      ],
    };
  }, [data]);

  if (!data.actual.length) {
    return <Empty description="暂无预测数据" />;
  }

  return <EChartView option={option} height={400} />;
}
