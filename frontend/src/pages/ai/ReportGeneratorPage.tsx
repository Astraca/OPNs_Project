import { ArrowLeftOutlined, FileTextOutlined } from "@ant-design/icons";
import { Button, Card, Input, Modal, Select, Space, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listModels } from "../../api/models";
import { generateReport } from "../../api/reports";
import type { MLModel } from "../../types/model";
import type { Report } from "../../types/report";


export default function ReportGeneratorPage() {
  const navigate = useNavigate();
  const [models, setModels] = useState<MLModel[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [reportTitle, setReportTitle] = useState("");
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<Report | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        setModels(await listModels());
      } catch { /* ignore */ }
    }
    void load();
  }, []);

  async function handleGenerate() {
    if (!selectedModelId) return;
    setGenerating(true);
    try {
      const report = await generateReport(
        selectedModelId,
        reportTitle || undefined,
      );
      setResult(report);
      message.success("实验报告已生成");
    } catch {
      message.error("报告生成失败");
    } finally {
      setGenerating(false);
    }
  }

  const selectedModel = models.find((m) => m.id === selectedModelId);

  return (
    <main>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>实验报告生成器</Typography.Title>
        <Button
          icon={<ArrowLeftOutlined />}
          style={{ borderColor: "#1677ff", color: "#1677ff" }}
          onClick={() => navigate("/reports")}
        >
          返回
        </Button>
      </div>

      <Card>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <Space wrap>
            <Select
              placeholder="选择模型"
              style={{ width: 360 }}
              value={selectedModelId}
              onChange={(v) => {
                setSelectedModelId(v);
                const m = models.find((mm) => mm.id === v);
                setReportTitle(m ? `${m.model_name} 实验报告` : "");
              }}
              options={models.map((m) => ({
                label: `${m.model_name} (${m.algorithm}, ${m.task_type === "regression" ? "回归" : "分类"})`,
                value: m.id,
              }))}
            />
          </Space>

          <Input
            placeholder="报告标题（可选）"
            value={reportTitle}
            onChange={(e) => setReportTitle(e.target.value)}
            style={{ maxWidth: 480 }}
          />

          {selectedModel && (
            <Typography.Text type="secondary">
              将基于模型「{selectedModel.model_name}」的各项指标和元数据自动生成实验报告。
            </Typography.Text>
          )}

          <Button
            type="primary"
            icon={<FileTextOutlined />}
            loading={generating}
            disabled={!selectedModelId}
            onClick={handleGenerate}
          >
            生成实验报告
          </Button>
        </Space>
      </Card>

      {result && (
        <Card title="报告预览" style={{ marginTop: 16 }}>
          <Typography.Paragraph style={{ whiteSpace: "pre-line", maxHeight: 360, overflow: "auto" }}>
            {result.content}
          </Typography.Paragraph>
          <Button
            type="primary"
            style={{ marginTop: 12 }}
            onClick={() => setPreviewOpen(true)}
          >
            查看完整报告
          </Button>
        </Card>
      )}

      <Modal
        title={result?.title}
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        footer={null}
        width={720}
      >
        <Typography.Paragraph style={{ whiteSpace: "pre-line", maxHeight: 520, overflow: "auto" }}>
          {result?.content}
        </Typography.Paragraph>
      </Modal>
    </main>
  );
}
