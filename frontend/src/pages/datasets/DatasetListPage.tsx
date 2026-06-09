import { DeleteOutlined, EyeOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Popconfirm, Space, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { deleteDataset, listDatasets } from "../../api/datasets";
import type { Dataset } from "../../types/dataset";
import "./DatasetPages.css";


export default function DatasetListPage() {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadDatasets() {
    setLoading(true);
    try {
      setDatasets(await listDatasets());
    } catch {
      message.error("数据集列表加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteDataset(id);
      message.success("数据集已删除");
      await loadDatasets();
    } catch {
      message.error("删除失败");
    }
  }

  useEffect(() => {
    void loadDatasets();
  }, []);

  const columns: ColumnsType<Dataset> = [
    { title: "名称", dataIndex: "name" },
    { title: "任务类型", dataIndex: "task_type" },
    { title: "样本数", dataIndex: "sample_count" },
    { title: "字段数", dataIndex: "feature_count" },
    {
      title: "目标字段",
      dataIndex: "target_columns",
      render: (targets: string[]) =>
        targets.length ? targets.map((target) => <Tag key={target}>{target}</Tag>) : "-",
    },
    {
      title: "操作",
      key: "actions",
      render: (_, record) => (
        <Space>
          <Button icon={<EyeOutlined />} onClick={() => navigate(`/datasets/${record.id}`)}>
            查看
          </Button>
          <Popconfirm title="确认删除该数据集？" onConfirm={() => void handleDelete(record.id)}>
            <Button danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <main>
      <div className="dataset-toolbar">
        <Typography.Title level={3}>数据集</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/datasets/create")}>
          新建数据集
        </Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={datasets} loading={loading} />
    </main>
  );
}
