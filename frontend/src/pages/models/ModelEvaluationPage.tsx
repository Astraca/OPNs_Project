import { Button, Descriptions, Table, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getModel, getModelMetrics } from "../../api/models";
import type { MLModel, ModelMetric } from "../../types/model";
import "./ModelPages.css";


type MetricRow = {
  target_name: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
};

export default function ModelEvaluationPage() {
  const { id } = useParams();
  const modelId = Number(id);
  const navigate = useNavigate();
  const [model, setModel] = useState<MLModel | null>(null);
  const [metrics, setMetrics] = useState<ModelMetric[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadModel() {
      setLoading(true);
      try {
        const [nextModel, nextMetrics] = await Promise.all([getModel(modelId), getModelMetrics(modelId)]);
        setModel(nextModel);
        setMetrics(nextMetrics);
      } catch {
        message.error("模型评估加载失败");
      } finally {
        setLoading(false);
      }
    }

    if (Number.isFinite(modelId)) {
      void loadModel();
    }
  }, [modelId]);

  const rows = useMemo(() => {
    const grouped = new Map<string, MetricRow>();
    metrics.forEach((metric) => {
      const target = metric.target_name ?? "overall";
      const row = grouped.get(target) ?? { target_name: target };
      row[metric.metric_name as keyof MetricRow] = metric.metric_value as never;
      grouped.set(target, row);
    });
    return Array.from(grouped.values());
  }, [metrics]);

  const columns: ColumnsType<MetricRow> = [
    { title: "标签", dataIndex: "target_name" },
    { title: "Accuracy", dataIndex: "accuracy", render: (value: number | undefined) => value?.toFixed(4) ?? "-" },
    { title: "Precision", dataIndex: "precision", render: (value: number | undefined) => value?.toFixed(4) ?? "-" },
    { title: "Recall", dataIndex: "recall", render: (value: number | undefined) => value?.toFixed(4) ?? "-" },
    { title: "F1", dataIndex: "f1", render: (value: number | undefined) => value?.toFixed(4) ?? "-" },
  ];

  return (
    <main>
      <div className="model-toolbar">
        <Typography.Title level={3}>模型评估</Typography.Title>
        <Button onClick={() => navigate("/models")}>返回模型列表</Button>
      </div>
      {model && (
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="模型名称">{model.model_name}</Descriptions.Item>
          <Descriptions.Item label="算法">{model.algorithm}</Descriptions.Item>
          <Descriptions.Item label="目标字段">{model.target_columns.join(", ")}</Descriptions.Item>
          <Descriptions.Item label="特征数">{model.feature_columns.length}</Descriptions.Item>
          <Descriptions.Item label="配对方式">{model.pairing_method ?? "-"}</Descriptions.Item>
          <Descriptions.Item label="模型目录">{model.model_file_path ?? "-"}</Descriptions.Item>
        </Descriptions>
      )}
      <section className="model-section">
        <Typography.Title level={4}>分类指标</Typography.Title>
        <Table rowKey="target_name" columns={columns} dataSource={rows} loading={loading} />
      </section>
    </main>
  );
}
