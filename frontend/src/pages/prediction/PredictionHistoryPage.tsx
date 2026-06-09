import { DownloadOutlined, EyeOutlined, FileTextOutlined } from "@ant-design/icons";
import { Button, Descriptions, Modal, Space, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";

import { generatePredictionExplanation } from "../../api/ai";
import { getPredictionDetail, listPredictionJobs } from "../../api/predictions";
import { listModels } from "../../api/models";
import AIReportPanel from "../ai/AIReportPanel";
import type { AIAnalysisReport } from "../../types/ai";
import type { MLModel } from "../../types/model";
import type { PredictionJob } from "../../types/prediction";
import "./PredictionPages.css";


const JOB_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  single: { label: "IgAN 单病例", color: "blue" },
  batch: { label: "IgAN 批量", color: "cyan" },
  regression_single: { label: "回归单样本", color: "orange" },
  regression_batch: { label: "回归批量", color: "gold" },
};

export default function PredictionHistoryPage() {
  const [jobs, setJobs] = useState<PredictionJob[]>([]);
  const [modelMap, setModelMap] = useState<Map<number, string>>(new Map());
  const [aiReport, setAiReport] = useState<AIAnalysisReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  useEffect(() => {
    async function loadJobs() {
      setLoading(true);
      try {
        const [jobData, modelData] = await Promise.all([
          listPredictionJobs(),
          listModels(),
        ]);
        setJobs(jobData);
        const map = new Map<number, string>();
        modelData.forEach((m) => map.set(m.id, m.model_name));
        setModelMap(map);
      } catch {
        message.error("预测历史加载失败");
      } finally {
        setLoading(false);
      }
    }
    void loadJobs();
  }, []);

  async function handleViewDetail(jobId: number) {
    try {
      const data = await getPredictionDetail(jobId);
      setDetail(data);
      setDetailOpen(true);
    } catch {
      message.error("预测详情加载失败");
    }
  }

  async function handleGenerateExplanation(jobId: number) {
    try {
      setAiReport(await generatePredictionExplanation(jobId));
      message.success("AI 预测说明已生成");
    } catch {
      message.error("AI 预测说明生成失败");
    }
  }

  function handleDownload(jobId: number) {
    window.open(`/api/predictions/batch/${jobId}/download`, "_blank");
  }

  const columns: ColumnsType<PredictionJob> = [
    { title: "ID", dataIndex: "id", width: 60 },
    {
      title: "模型",
      dataIndex: "model_id",
      width: 140,
      render: (id: number) => modelMap.get(id) || `#${id}`,
    },
    {
      title: "类型",
      dataIndex: "job_type",
      width: 130,
      render: (value: string) => {
        const cfg = JOB_TYPE_LABELS[value] ?? { label: value, color: "default" };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 80,
      render: (value: string) => (
        <Tag color={value === "completed" ? "green" : value === "failed" ? "red" : "blue"}>
          {value === "completed" ? "完成" : value === "failed" ? "失败" : value}
        </Tag>
      ),
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      render: (value: string) => (value ? new Date(value).toLocaleString("zh-CN") : "-"),
    },
    {
      title: "操作",
      key: "actions",
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record.id)}>
            详情
          </Button>
          <Button
            size="small"
            icon={<FileTextOutlined />}
            onClick={() => handleGenerateExplanation(record.id)}
          >
            说明
          </Button>
          {(record.job_type === "batch" || record.job_type === "regression_batch") && (
            <Button
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record.id)}
            >
              导出
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <main>
      <Typography.Title level={3}>预测历史</Typography.Title>
      <AIReportPanel report={aiReport} />
      <Table rowKey="id" columns={columns} dataSource={jobs} loading={loading} />

      <Modal
        title={`预测详情 #${detail?.id ?? ""}`}
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={null}
        width={720}
      >
        {detail && (
          <>
            <Descriptions bordered size="small" column={2} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="类型">
                {JOB_TYPE_LABELS[detail.job_type as string]?.label ?? String(detail.job_type)}
              </Descriptions.Item>
              <Descriptions.Item label="状态">{String(detail.status)}</Descriptions.Item>
              <Descriptions.Item label="样本数">{String(detail.sample_count)}</Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {detail.created_at ? new Date(detail.created_at as string).toLocaleString("zh-CN") : "-"}
              </Descriptions.Item>
            </Descriptions>
            {Array.isArray(detail.results) && detail.results.length > 0 && (
              <Table
                rowKey="sample_index"
                dataSource={detail.results as Record<string, unknown>[]}
                columns={[
                  { title: "#", dataIndex: "sample_index", width: 50 },
                  {
                    title: "输入",
                    dataIndex: "input",
                    ellipsis: true,
                    render: (v: unknown) =>
                      typeof v === "object" ? JSON.stringify(v).slice(0, 200) : String(v ?? ""),
                  },
                  {
                    title: "预测结果",
                    dataIndex: "prediction",
                    render: (v: unknown) =>
                      typeof v === "object" ? (
                        <Space wrap size={[0, 4]}>
                          {Object.entries(v as Record<string, unknown>).map(([k, val]) => (
                            <Tag key={k}>
                              {k}: {typeof val === "object" ? JSON.stringify(val) : String(val ?? "-")}
                            </Tag>
                          ))}
                        </Space>
                      ) : (
                        String(v ?? "-")
                      ),
                  },
                ]}
                pagination={false}
                size="small"
                scroll={{ y: 360 }}
              />
            )}
          </>
        )}
      </Modal>
    </main>
  );
}
