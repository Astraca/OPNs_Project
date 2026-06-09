import { Empty } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { MissingValuesChartData } from "../../types/dataset";
import { displayFieldName } from "../../utils/fieldNames";
import EChartView from "./EChartView";


type MissingValuesBarChartProps = {
  data: MissingValuesChartData;
};

export default function MissingValuesBarChart({ data }: MissingValuesBarChartProps) {
  const items = data.items.filter((item) => item.missing_count > 0);

  const option = useMemo<EChartsOption>(
    () => ({
      tooltip: {
        trigger: "axis",
        valueFormatter: (value) => `${value}`,
      },
      grid: { left: 56, right: 24, top: 28, bottom: 96 },
      xAxis: {
        type: "category",
        data: items.map((item) => displayFieldName(item.column_name)),
        axisLabel: { rotate: 35, interval: 0 },
      },
      yAxis: { type: "value", name: "缺失数" },
      series: [
        {
          type: "bar",
          data: items.map((item) => item.missing_count),
          itemStyle: { color: "#3b82f6" },
        },
      ],
    }),
    [items],
  );

  if (!items.length) {
    return <Empty description="暂无缺失值" />;
  }

  return <EChartView option={option} />;
}
