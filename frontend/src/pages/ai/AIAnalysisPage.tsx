import { BarChartOutlined, DatabaseOutlined, FileTextOutlined } from "@ant-design/icons";
import { Button, Card, Select, Space, Spin, Typography, message } from "antd";
import { useEffect, useState } from "react";

import { generateDatasetAnalysis } from "../../api/ai";
import { listDatasets } from "../../api/datasets";
import { generateModelAnalysis } from "../../api/ai";
import { listModels } from "../../api/models";
import AIReportPanel from "./AIReportPanel";
import type { AIAnalysisReport } from "../../types/ai";
import type { Dataset } from "../../types/dataset";
import type { MLModel } from "../../types/model";


type TabMode = "dataset" | "model";

export default function AIAnalysisPage() {
  const [mode, setMode] = useState<TabMode>("dataset");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [models, setModels] = useState<MLModel[]>([]);
  const [selectedDsId, setSelectedDsId] = useState<number | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [report, setReport] = useState<AIAnalysisReport | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [ds, md] = await Promise.all([
          listDatasets(),
          listModels(),
        ]);
        setDatasets(ds.filter((d) => d.file_path));
        setModels(md);
      } catch { /* ignore */ }
    }
    void load();
  }, []);

  async function handleGenerateDs() {
    if (!selectedDsId) return;
    setGenerating(true);
    try {
      setReport(await generateDatasetAnalysis(selectedDsId));
      message.success("AI 数据分析已生成");
    } catch {
      message.error("生成失败");
    } finally {
      setGenerating(false);
    }
  }

  async function handleGenerateModel() {
    if (!selectedModelId) return;
    setGenerating(true);
    try {
      setReport(await generateModelAnalysis(selectedModelId));
      message.success("AI 模型分析已生成");
    } catch {
      message.error("生成失败");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <main>
      <Typography.Title level={3}>AI 辅助分析</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Button
            type={mode === "dataset" ? "primary" : "default"}
            icon={<DatabaseOutlined />}
            onClick={() => { setMode("dataset"); setReport(null); }}
          >
            数据集分析
          </Button>
          <Button
            type={mode === "model" ? "primary" : "default"}
            icon={<BarChartOutlined />}
            onClick={() => { setMode("model"); setReport(null); }}
          >
            模型分析
          </Button>
        </Space>
      </Card>

      {mode === "dataset" && (
        <Card title="数据集 AI 分析">
          <Space direction="vertical" style={{ width: "100%" }}>
            <Space>
              <Select
                placeholder="选择数据集"
                style={{ width: 360 }}
                value={selectedDsId}
                onChange={setSelectedDsId}
                options={datasets.map((d) => ({
                  label: `${d.name} (${d.sample_count} 行)`,
                  value: d.id,
                }))}
              />
              <Button
                type="primary"
                icon={<FileTextOutlined />}
                loading={generating}
                disabled={!selectedDsId}
                onClick={handleGenerateDs}
              >
                生成分析
              </Button>
            </Space>
            {generating && <Spin tip="正在生成 AI 分析..." />}
            <AIReportPanel report={report} />
          </Space>
        </Card>
      )}

      {mode === "model" && (
        <Card title="模型 AI 分析">
          <Space direction="vertical" style={{ width: "100%" }}>
            <Space>
              <Select
                placeholder="选择模型"
                style={{ width: 360 }}
                value={selectedModelId}
                onChange={setSelectedModelId}
                options={models.map((m) => ({
                  label: `${m.model_name} (${m.algorithm})`,
                  value: m.id,
                }))}
              />
              <Button
                type="primary"
                icon={<FileTextOutlined />}
                loading={generating}
                disabled={!selectedModelId}
                onClick={handleGenerateModel}
              >
                生成分析
              </Button>
            </Space>
            {generating && <Spin tip="正在生成 AI 分析..." />}
            <AIReportPanel report={report} />
          </Space>
        </Card>
      )}
    </main>
  );
}
