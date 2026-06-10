import {
  BarChartOutlined,
  DeleteOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Descriptions,
  Popconfirm,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { deleteModel, getModel, getModelMetadata, getModelMetrics } from "../../api/models";
import type { MLModel, ModelMetric } from "../../types/model";
import { displayFieldName, displayPairingMethod } from "../../utils/fieldNames";
import "./ModelPages.css";


type MetricRow = {
  target_name: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
  mae?: number;
  rmse?: number;
  r2?: number;
  mape?: number;
};

export default function ModelDetailPage() {
  const { id } = useParams();
  const modelId = Number(id);
  const navigate = useNavigate();
  const [model, setModel] = useState<MLModel | null>(null);
  const [metrics, setMetrics] = useState<ModelMetric[]>([]);
  const [metadata, setMetadata] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [m, met, meta] = await Promise.all([
          getModel(modelId),
          getModelMetrics(modelId),
          getModelMetadata(modelId).catch(() => null),
        ]);
        setModel(m);
        setMetrics(met);
        setMetadata(meta);
      } catch {
        message.error("模型详情加载失败");
      } finally {
        setLoading(false);
      }
    }
    if (Number.isFinite(modelId)) void load();
  }, [modelId]);

  async function handleDelete() {
    try {
      await deleteModel(modelId);
      message.success("模型已删除");
      navigate("/models", { replace: true });
    } catch {
      message.error("删除失败");
    }
  }

  const isRegression = model?.task_type === "regression";

  const metricRows: MetricRow[] = (() => {
    if (isRegression) {
      const row: MetricRow = { target_name: model?.target_columns[0] ?? "target" };
      metrics.forEach((m) => {
        row[m.metric_name as keyof MetricRow] = m.metric_value as never;
      });
      return [row];
    }
    const grouped = new Map<string, MetricRow>();
    metrics.forEach((m) => {
      const target = m.target_name ?? "overall";
      const row = grouped.get(target) ?? { target_name: target };
      row[m.metric_name as keyof MetricRow] = m.metric_value as never;
      grouped.set(target, row);
    });
    return Array.from(grouped.values());
  })();

  const classificationColumns: ColumnsType<MetricRow> = [
    { title: "标签", dataIndex: "target_name" },
    { title: "Accuracy", dataIndex: "accuracy", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "Precision", dataIndex: "precision", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "Recall", dataIndex: "recall", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "F1", dataIndex: "f1", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
  ];

  const regressionColumns: ColumnsType<MetricRow> = [
    { title: "目标", dataIndex: "target_name" },
    { title: "MAE", dataIndex: "mae", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "RMSE", dataIndex: "rmse", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "R²", dataIndex: "r2", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "MAPE", dataIndex: "mape", render: (v: number | undefined) => v != null ? `${v.toFixed(2)}%` : "-" },
  ];

  return (
    <main>
      <div className="model-toolbar">
        <Typography.Title level={3}>{model?.model_name ?? "模型详情"}</Typography.Title>
        <Space>
          <Button
            type="primary"
            icon={<BarChartOutlined />}
            onClick={() => navigate(`/models/${modelId}/evaluation`)}
          >
            完整评估
          </Button>
          <Button
            icon={<ThunderboltOutlined />}
            onClick={() =>
              navigate(
                isRegression
                  ? "/prediction/regression/single"
                  : "/prediction/igan/single",
              )
            }
          >
            开始预测
          </Button>
          <Popconfirm title="确定删除此模型？" onConfirm={handleDelete}>
            <Button danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      </div>

      {model && (
        <Card className="model-section">
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="模型名称">{model.model_name}</Descriptions.Item>
            <Descriptions.Item label="算法">
              <Tag color="blue">{model.algorithm}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="任务类型">
              <Tag color={isRegression ? "orange" : "green"}>
                {isRegression ? "回归" : "分类"}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="OPNs 启用">
              {model.opns_enabled ? <Tag color="blue">是</Tag> : <Tag>否</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="目标字段">
              {model.target_columns.map(displayFieldName).join(", ")}
            </Descriptions.Item>
            <Descriptions.Item label="配对方式">{displayPairingMethod(model.pairing_method)}</Descriptions.Item>
            <Descriptions.Item label="特征数">{model.feature_columns.length}</Descriptions.Item>
            <Descriptions.Item label="数据集 ID">{model.dataset_id}</Descriptions.Item>
            <Descriptions.Item label="模型目录" span={2}>
              <Typography.Text code>{model.model_file_path ?? "-"}</Typography.Text>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间" span={2}>
              {new Date(model.created_at).toLocaleString("zh-CN")}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      <Card title="模型指标" className="model-section">
        <Table
          rowKey="target_name"
          columns={isRegression ? regressionColumns : classificationColumns}
          dataSource={metricRows}
          loading={loading}
          pagination={false}
        />
      </Card>

      {model && (
        <Card title="特征列表" className="model-section">
          <Space wrap>
            {model.feature_columns.map((f) => (
              <Tag key={f}>{displayFieldName(f)}</Tag>
            ))}
          </Space>
        </Card>
      )}

      {metadata && (
        <Card title="训练元数据" className="model-section">
          <Descriptions bordered size="small" column={2}>
            {Object.entries(metadata).map(([key, value]) => (
              <Descriptions.Item key={key} label={key}>
                {typeof value === "object"
                  ? JSON.stringify(value)
                  : String(value ?? "-")}
              </Descriptions.Item>
            ))}
          </Descriptions>
        </Card>
      )}
    </main>
  );
}
