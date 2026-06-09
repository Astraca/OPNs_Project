import { DeleteOutlined, EyeOutlined, FileTextOutlined } from "@ant-design/icons";
import { Button, Modal, Popconfirm, Space, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";

import { deleteReport, generateReport, listReports } from "../../api/reports";
import { listModels } from "../../api/models";
import type { MLModel } from "../../types/model";
import type { Report } from "../../types/report";
import "./ReportPages.css";


export default function ReportListPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const [repData, modData] = await Promise.all([
        listReports(),
        listModels(),
      ]);
      setReports(repData);
      setModels(modData);
    } catch {
      message.error("加载报告列表失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function handleGenerate(modelId: number) {
    setGenerating(true);
    try {
      const model = models.find((m) => m.id === modelId);
      const report = await generateReport(modelId, model ? `${model.model_name} 实验报告` : undefined);
      setReports((prev) => [report, ...prev]);
      message.success("报告已生成");
    } catch {
      message.error("报告生成失败");
    } finally {
      setGenerating(false);
    }
  }

  async function handleDelete(reportId: number) {
    try {
      await deleteReport(reportId);
      setReports((prev) => prev.filter((r) => r.id !== reportId));
      message.success("报告已删除");
    } catch {
      message.error("删除失败");
    }
  }

  const columns: ColumnsType<Report> = [
    { title: "标题", dataIndex: "title", ellipsis: true },
    {
      title: "类型",
      dataIndex: "report_type",
      render: (value: string) => <Tag color="blue">{value === "experiment" ? "实验报告" : value}</Tag>,
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      render: (value: string) => new Date(value).toLocaleString("zh-CN"),
    },
    {
      title: "操作",
      key: "actions",
      render: (_, record) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={() => setSelectedReport(record)}
          >
            查看
          </Button>
          <Popconfirm title="确定删除此报告？" onConfirm={() => handleDelete(record.id)}>
            <Button danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <main>
      <div className="report-toolbar">
        <Typography.Title level={3}>分析报告</Typography.Title>
        <Space>
          <Typography.Text type="secondary">选择模型生成实验报告：</Typography.Text>
          <Button
            type="primary"
            icon={<FileTextOutlined />}
            loading={generating}
            onClick={() => {
              if (models.length === 0) {
                message.warning("暂无已训练的模型");
                return;
              }
              // Use first model or let user pick
              handleGenerate(models[0].id);
            }}
            disabled={!models.length}
          >
            {models.length ? `为「${models[0].model_name}」生成报告` : "暂无模型"}
          </Button>
        </Space>
      </div>

      {models.length > 1 && (
        <Space wrap style={{ marginBottom: 16 }}>
          <Typography.Text type="secondary">或者为其他模型生成：</Typography.Text>
          {models.slice(1).map((m) => (
            <Button
              key={m.id}
              size="small"
              loading={generating}
              onClick={() => handleGenerate(m.id)}
            >
              {m.model_name}
            </Button>
          ))}
        </Space>
      )}

      <Table rowKey="id" columns={columns} dataSource={reports} loading={loading} />

      <Modal
        title={selectedReport?.title}
        open={!!selectedReport}
        onCancel={() => setSelectedReport(null)}
        footer={null}
        width={720}
      >
        {selectedReport && (
          <Typography.Paragraph
            style={{ whiteSpace: "pre-line", maxHeight: 520, overflow: "auto" }}
          >
            {selectedReport.content}
          </Typography.Paragraph>
        )}
      </Modal>
    </main>
  );
}
