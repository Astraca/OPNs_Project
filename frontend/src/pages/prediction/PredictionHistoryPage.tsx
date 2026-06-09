import { Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";

import { listPredictionJobs } from "../../api/predictions";
import type { PredictionJob } from "../../types/prediction";
import "./PredictionPages.css";


export default function PredictionHistoryPage() {
  const [jobs, setJobs] = useState<PredictionJob[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadJobs() {
      setLoading(true);
      try {
        setJobs(await listPredictionJobs());
      } catch {
        message.error("预测历史加载失败");
      } finally {
        setLoading(false);
      }
    }

    void loadJobs();
  }, []);

  const columns: ColumnsType<PredictionJob> = [
    { title: "ID", dataIndex: "id" },
    { title: "模型 ID", dataIndex: "model_id" },
    { title: "类型", dataIndex: "job_type" },
    { title: "状态", dataIndex: "status", render: (value: string) => <Tag color="green">{value}</Tag> },
    { title: "创建时间", dataIndex: "created_at" },
  ];

  return (
    <main>
      <Typography.Title level={3}>预测历史</Typography.Title>
      <Table rowKey="id" columns={columns} dataSource={jobs} loading={loading} />
    </main>
  );
}
