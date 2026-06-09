import { Alert, Button, Col, Row, Statistic, Table, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getCorrelationMatrixChart,
  getDatasetProfile,
  getLabelDistributionChart,
  getMissingValuesChart,
  getNumericStatisticsChart,
} from "../../api/datasets";
import CorrelationHeatmap from "../../components/Charts/CorrelationHeatmap";
import LabelDistributionChart from "../../components/Charts/LabelDistributionChart";
import MissingValuesBarChart from "../../components/Charts/MissingValuesBarChart";
import type {
  CorrelationMatrixData,
  DatasetProfile,
  LabelDistributionData,
  MissingValuesChartData,
  NumericStatisticsItem,
} from "../../types/dataset";
import "./DatasetPages.css";


export default function DatasetProfilePage() {
  const { id } = useParams();
  const datasetId = Number(id);
  const navigate = useNavigate();
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [missingValues, setMissingValues] = useState<MissingValuesChartData | null>(null);
  const [labelDistribution, setLabelDistribution] = useState<LabelDistributionData | null>(null);
  const [correlation, setCorrelation] = useState<CorrelationMatrixData | null>(null);
  const [numericStats, setNumericStats] = useState<NumericStatisticsItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      setLoading(true);
      try {
        const [nextProfile, nextMissing, nextDistribution, nextCorrelation, nextStats] = await Promise.all([
          getDatasetProfile(datasetId),
          getMissingValuesChart(datasetId),
          getLabelDistributionChart(datasetId),
          getCorrelationMatrixChart(datasetId),
          getNumericStatisticsChart(datasetId),
        ]);
        setProfile(nextProfile);
        setMissingValues(nextMissing);
        setLabelDistribution(nextDistribution);
        setCorrelation(nextCorrelation);
        setNumericStats(nextStats.items);
      } catch {
        message.error("数据分析加载失败，请确认已上传数据文件");
      } finally {
        setLoading(false);
      }
    }

    if (Number.isFinite(datasetId)) {
      void loadProfile();
    }
  }, [datasetId]);

  const numericColumns: ColumnsType<NumericStatisticsItem> = [
    { title: "字段", dataIndex: "column_name" },
    { title: "均值", dataIndex: "mean", render: (value: number | null) => value?.toFixed(4) ?? "-" },
    { title: "标准差", dataIndex: "std", render: (value: number | null) => value?.toFixed(4) ?? "-" },
    { title: "最小值", dataIndex: "min_value", render: (value: number | null) => value?.toFixed(4) ?? "-" },
    { title: "最大值", dataIndex: "max_value", render: (value: number | null) => value?.toFixed(4) ?? "-" },
    { title: "缺失值", dataIndex: "missing_count" },
  ];

  return (
    <main>
      <div className="dataset-toolbar">
        <div>
          <Typography.Title level={3}>数据分析</Typography.Title>
          <Typography.Text type="secondary">{profile?.dataset.name ?? "数据集质量与分布统计"}</Typography.Text>
        </div>
        <Button onClick={() => navigate(`/datasets/${datasetId}`)}>返回详情</Button>
      </div>

      <Alert
        type="info"
        showIcon
        message="本页图表仅用于数据质量检查和科研建模准备。"
        className="dataset-section"
      />

      <Row gutter={[16, 16]} className="dataset-section">
        <Col xs={24} md={8}>
          <Statistic title="样本数" value={profile?.dataset.sample_count ?? 0} loading={loading} />
        </Col>
        <Col xs={24} md={8}>
          <Statistic title="字段数" value={profile?.dataset.feature_count ?? 0} loading={loading} />
        </Col>
        <Col xs={24} md={8}>
          <Statistic title="目标字段数" value={profile?.dataset.target_columns.length ?? 0} loading={loading} />
        </Col>
      </Row>

      <section className="dataset-chart-section">
        <Typography.Title level={4}>缺失值统计</Typography.Title>
        {missingValues && <MissingValuesBarChart data={missingValues} />}
      </section>

      <section className="dataset-chart-section">
        <Typography.Title level={4}>标签分布</Typography.Title>
        {labelDistribution && <LabelDistributionChart data={labelDistribution} />}
      </section>

      <section className="dataset-chart-section">
        <Typography.Title level={4}>相关性热力图</Typography.Title>
        {correlation && <CorrelationHeatmap data={correlation} />}
      </section>

      <section className="dataset-chart-section">
        <Typography.Title level={4}>数值字段统计</Typography.Title>
        <Table
          rowKey="column_name"
          columns={numericColumns}
          dataSource={numericStats}
          loading={loading}
          scroll={{ x: true }}
        />
      </section>
    </main>
  );
}
