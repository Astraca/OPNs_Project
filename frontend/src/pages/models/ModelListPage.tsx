import { BarChartOutlined, DeleteOutlined, EyeOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Popconfirm, Space, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { deleteModel, listModels } from "../../api/models";
import type { MLModel } from "../../types/model";
import { displayFieldName, displayPairingMethod } from "../../utils/fieldNames";
import "./ModelPages.css";


const TASK_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  classification: { label: "单标签分类", color: "green" },
  multi_output_classification: { label: "多标签分类", color: "blue" },
  regression: { label: "回归", color: "orange" },
};

export default function ModelListPage() {
  const navigate = useNavigate();
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadModels() {
    setLoading(true);
    try {
      setModels(await listModels());
    } catch {
      message.error("模型列表加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadModels();
  }, []);

  async function handleDelete(modelId: number) {
    try {
      await deleteModel(modelId);
      message.success("模型已删除");
      setModels((prev) => prev.filter((m) => m.id !== modelId));
    } catch {
      message.error("删除失败");
    }
  }

  const columns: ColumnsType<MLModel> = [
    { title: "名称", dataIndex: "model_name", minWidth: 140, ellipsis: true },
    {
      title: "任务类型", dataIndex: "task_type", minWidth: 100,
      render: (value: string) => {
        const info = TASK_TYPE_LABELS[value] ?? { label: value, color: "default" };
        return <Tag color={info.color}>{info.label}</Tag>;
      },
    },
    { title: "算法", dataIndex: "algorithm", minWidth: 100, render: (value: string) => <Tag color="blue">{value}</Tag> },
    {
      title: "配对方式", dataIndex: "pairing_method", minWidth: 120,
      render: (value: string | null) => displayPairingMethod(value),
    },
    {
      title: "目标字段", dataIndex: "target_columns", width: 160,
      onCell: () => ({ style: { maxWidth: 160 } }),
      render: (targets: string[]) => (
        <Typography.Text ellipsis={{ tooltip: targets.map(displayFieldName).join(", ") }}>
          {targets.map(displayFieldName).join(", ")}
        </Typography.Text>
      ),
    },
    { title: "特征数", dataIndex: "feature_columns", minWidth: 100, render: (features: string[]) => features.length },
    {
      title: "操作", key: "actions", minWidth: 180,
      render: (_, record) => (
        <Space>
          <Button icon={<EyeOutlined />} onClick={() => navigate(`/models/${record.id}`)}>详情</Button>
          <Button icon={<BarChartOutlined />} onClick={() => navigate(`/models/${record.id}/evaluation`)}>评估</Button>
          <Popconfirm title="确定删除此模型？" onConfirm={() => handleDelete(record.id)}>
            <Button danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <main>
      <div className="model-toolbar">
        <Typography.Title level={3}>模型训练</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/models/train")}>
          训练模型
        </Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={models} loading={loading} scroll={{ x: "max-content" }} />
    </main>
  );
}
