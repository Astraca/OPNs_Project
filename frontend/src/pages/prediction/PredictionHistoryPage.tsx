import { Button, Space, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";

import { listPredictionJobs } from "../../api/predictions";
import { generatePredictionExplanation } from "../../api/ai";
import AIReportPanel from "../ai/AIReportPanel";
import type { AIAnalysisReport } from "../../types/ai";
import type { PredictionJob } from "../../types/prediction";
import "./PredictionPages.css";


export default function PredictionHistoryPage() {
  const [jobs, setJobs] = useState<PredictionJob[]>([]);
  const [aiReport, setAiReport] = useState<AIAnalysisReport | null>(null);
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
    {
      title: "操作",
      key: "actions",
      render: (_, record) => (
        <Button onClick={() => void handleGenerateExplanation(record.id)}>生成说明</Button>
      ),
    },
  ];

  async function handleGenerateExplanation(jobId: number) {
    try {
      setAiReport(await generatePredictionExplanation(jobId));
      message.success("AI 预测说明已生成");
    } catch {
      message.error("AI 预测说明生成失败");
    }
  }

  return (
    <main>
      <Typography.Title level={3}>预测历史</Typography.Title>
      <Space direction="vertical" style={{ width: "100%" }}>
        <AIReportPanel report={aiReport} />
      </Space>
      <Table rowKey="id" columns={columns} dataSource={jobs} loading={loading} />
    </main>
  );
}
