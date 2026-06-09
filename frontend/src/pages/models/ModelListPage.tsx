import { BarChartOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Space, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listModels } from "../../api/models";
import type { MLModel } from "../../types/model";
import { displayFieldName } from "../../utils/fieldNames";
import "./ModelPages.css";


export default function ModelListPage() {
  const navigate = useNavigate();
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
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

    void loadModels();
  }, []);

  const columns: ColumnsType<MLModel> = [
    { title: "名称", dataIndex: "model_name" },
    { title: "算法", dataIndex: "algorithm", render: (value: string) => <Tag color="blue">{value}</Tag> },
    { title: "目标字段", dataIndex: "target_columns", render: (targets: string[]) => targets.map(displayFieldName).join(", ") },
    { title: "特征数", dataIndex: "feature_columns", render: (features: string[]) => features.length },
    {
      title: "操作",
      key: "actions",
      render: (_, record) => (
        <Space>
          <Button icon={<BarChartOutlined />} onClick={() => navigate(`/models/${record.id}/evaluation`)}>
            评估
          </Button>
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
      <Table rowKey="id" columns={columns} dataSource={models} loading={loading} />
    </main>
  );
}
