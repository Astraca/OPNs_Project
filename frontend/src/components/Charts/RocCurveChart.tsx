import { Empty, Tabs } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { RocCurveData } from "../../types/model";
import EChartView from "./EChartView";


type Props = {
  data: RocCurveData[];
};

export default function RocCurveChart({ data }: Props) {
  if (!data.length || data.every((d) => !d.curves.length)) {
    return <Empty description="暂无 ROC 数据" />;
  }

  return (
    <Tabs
      items={data.map((item) => ({
        key: item.target_name,
        label: item.target_name,
        children: <SingleRocCurve item={item} />,
      }))}
    />
  );
}

function SingleRocCurve({ item }: { item: RocCurveData }) {
  const option = useMemo<EChartsOption>(
    () => ({
      tooltip: { trigger: "item" },
      grid: { left: 56, right: 24, top: 36, bottom: 56 },
      xAxis: { type: "value", name: "FPR", min: 0, max: 1 },
      yAxis: { type: "value", name: "TPR", min: 0, max: 1 },
      series: [
        ...item.curves.map((curve) => ({
          type: "line" as const,
          data: curve.fpr.map((fpr, i) => [fpr, curve.tpr[i]]),
          name: `AUC=${curve.auc.toFixed(4)}`,
          smooth: true,
        })),
        {
          type: "line" as const,
          data: [[0, 0], [1, 1]],
          lineStyle: { type: "dashed" as const, color: "#ccc" },
          silent: true,
        },
      ],
    }),
    [item],
  );

  return <EChartView option={option} height={380} />;
}
