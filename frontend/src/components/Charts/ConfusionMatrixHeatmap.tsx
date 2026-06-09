import { Empty, Tabs } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { ConfusionMatrixData } from "../../types/model";
import EChartView from "./EChartView";


type Props = {
  data: ConfusionMatrixData[];
};

export default function ConfusionMatrixHeatmap({ data }: Props) {
  if (!data.length) {
    return <Empty description="暂无混淆矩阵数据" />;
  }

  return (
    <Tabs
      items={data.map((item) => ({
        key: item.target_name,
        label: item.target_name,
        children: <SingleConfusionMatrix item={item} />,
      }))}
    />
  );
}

function SingleConfusionMatrix({ item }: { item: ConfusionMatrixData }) {
  const heatData = item.matrix.flatMap((row, ri) =>
    row.map((value, ci) => [ci, ri, value]),
  );

  const option = useMemo<EChartsOption>(
    () => ({
      tooltip: { position: "top" },
      grid: { left: 56, right: 32, top: 32, bottom: 72 },
      xAxis: {
        type: "category",
        data: item.labels,
        name: "预测值",
        splitArea: { show: true },
      },
      yAxis: {
        type: "category",
        data: item.labels,
        name: "真实值",
        splitArea: { show: true },
      },
      visualMap: {
        min: 0,
        max: Math.max(...item.matrix.flat(), 1),
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 4,
      },
      series: [
        {
          type: "heatmap",
          data: heatData,
          label: { show: true },
        },
      ],
    }),
    [item, heatData],
  );

  return <EChartView option={option} height={320} />;
}
