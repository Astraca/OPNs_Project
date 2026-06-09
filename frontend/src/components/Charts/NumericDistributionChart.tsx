import { Empty, Tabs } from "antd";
import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import type { NumericDistributionData } from "../../types/dataset";
import { displayFieldName } from "../../utils/fieldNames";
import EChartView from "./EChartView";


type Props = {
  data: NumericDistributionData;
};

export default function NumericDistributionChart({ data }: Props) {
  const columns = data.columns;

  if (!columns.length) {
    return <Empty description="无数值特征可展示分布" />;
  }

  return (
    <Tabs
      items={columns.map((col) => ({
        key: col,
        label: displayFieldName(col),
        children: <SingleHistogram column={col} distribution={data.distributions[col]} />,
      }))}
    />
  );
}

function SingleHistogram({
  column,
  distribution,
}: {
  column: string;
  distribution: NumericDistributionData["distributions"][string];
}) {
  const option = useMemo<EChartsOption>(() => {
    const barData = distribution.bin_centers.map((center, i) => [center, distribution.counts[i]]);

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: unknown) => {
          const items = Array.isArray(params) ? params : [params];
          return items
            .map((p) => {
              const v = p as { value: number[] };
              const idx = distribution.bin_centers.indexOf(v.value[0]);
              const lo = distribution.bin_edges[idx]?.toFixed(4);
              const hi = distribution.bin_edges[idx + 1]?.toFixed(4);
              return `区间 [${lo}, ${hi})<br/>样本数：${v.value[1]}`;
            })
            .join("");
        },
      },
      grid: { left: 56, right: 24, top: 28, bottom: 48 },
      xAxis: {
        type: "value",
        name: displayFieldName(column),
        nameLocation: "middle" as const,
        nameGap: 32,
      },
      yAxis: { type: "value", name: "样本数" },
      series: [
        {
          type: "bar",
          data: barData,
          barWidth: "90%",
          itemStyle: {
            color: "#3b82f6",
            borderRadius: [2, 2, 0, 0],
          },
        },
      ],
    };
  }, [column, distribution]);

  return <EChartView option={option} height={340} />;
}
