import { Empty, Tabs } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { LabelDistributionData } from "../../types/dataset";
import { displayFieldName } from "../../utils/fieldNames";
import EChartView from "./EChartView";


type SingleLabelChartProps = {
  target: string;
  distribution: Record<string, number>;
};

function SingleLabelChart({ target, distribution }: SingleLabelChartProps) {
  const labels = Object.keys(distribution);
  const option = useMemo<EChartsOption>(
    () => ({
      tooltip: { trigger: "axis" },
      grid: { left: 48, right: 24, top: 36, bottom: 48 },
      xAxis: { type: "category", data: labels },
      yAxis: { type: "value", name: "样本数" },
      series: [
        {
          name: target,
          type: "bar",
          data: labels.map((label) => distribution[label]),
          itemStyle: { color: "#16a34a" },
        },
      ],
    }),
    [distribution, labels, target],
  );

  return <EChartView option={option} height={300} />;
}

type LabelDistributionChartProps = {
  data: LabelDistributionData;
};

export default function LabelDistributionChart({ data }: LabelDistributionChartProps) {
  const targets = Object.keys(data.distributions);

  if (!targets.length) {
    return <Empty description="暂无标签分布数据" />;
  }

  return (
    <Tabs
      items={targets.map((target) => ({
        key: target,
          label: displayFieldName(target),
        children: <SingleLabelChart target={target} distribution={data.distributions[target]} />,
      }))}
    />
  );
}
