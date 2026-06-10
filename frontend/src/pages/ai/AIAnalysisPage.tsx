import {
  ArrowLeftOutlined,
  BarChartOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { Alert, Button, Card, List, Select, Space, Spin, Tag, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { generateDatasetAnalysis, runPrivacyScan } from "../../api/ai";
import { listDatasets } from "../../api/datasets";
import { generateModelAnalysis } from "../../api/ai";
import { listModels } from "../../api/models";
import AIReportPanel from "./AIReportPanel";
import type { AIAnalysisReport, PrivacyFieldItem } from "../../types/ai";
import type { Dataset } from "../../types/dataset";
import type { MLModel } from "../../types/model";


type TabMode = "dataset" | "model";

type AIAnalysisPageProps = {
  initialMode?: TabMode;
};

const RISK_COLORS: Record<string, string> = {
  high: "red",
  medium: "orange",
  low: "green",
};

const CLASS_LABELS: Record<string, string> = {
  direct_identifier: "身份标识",
  quasi_identifier: "准标识符",
  sensitive_medical: "医学敏感",
  normal_modeling: "正常",
};

export default function AIAnalysisPage({ initialMode = "dataset" }: AIAnalysisPageProps) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryMode = searchParams.get("mode") === "model" ? "model" : null;
  const [mode, setMode] = useState<TabMode>(queryMode ?? initialMode);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [models, setModels] = useState<MLModel[]>([]);
  const [selectedDsId, setSelectedDsId] = useState<number | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [report, setReport] = useState<AIAnalysisReport | null>(null);
  const [generating, setGenerating] = useState(false);

  // Privacy scan state
  const [privacyFields, setPrivacyFields] = useState<PrivacyFieldItem[]>([]);
  const [privacySummary, setPrivacySummary] = useState<string>("");
  const [hasDirectIds, setHasDirectIds] = useState(false);
  const [scanning, setScanning] = useState(false);

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

  async function handleDatasetChange(id: number) {
    setSelectedDsId(id);
    setReport(null);
    setPrivacyFields([]);
    setPrivacySummary("");
    setHasDirectIds(false);
    if (id == null) return;

    setScanning(true);
    try {
      const result = await runPrivacyScan(id);
      setPrivacyFields(result.classifications);
      setPrivacySummary(result.risk_summary);
      setHasDirectIds(result.has_direct_identifiers);
    } catch {
      // Non-blocking
    } finally {
      setScanning(false);
    }
  }

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

  const highRiskFields = privacyFields.filter(
    (f) => f.classification === "direct_identifier",
  );
  const mediumRiskFields = privacyFields.filter(
    (f) => f.classification === "quasi_identifier" || f.classification === "sensitive_medical",
  );

  return (
    <main>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>AI 辅助分析</Typography.Title>
        <Button
          icon={<ArrowLeftOutlined />}
          style={{ borderColor: "#1677ff", color: "#1677ff" }}
          onClick={() => navigate("/dashboard")}
        >
          返回
        </Button>
      </div>

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
                onChange={handleDatasetChange}
                options={datasets.map((d) => ({
                  label: `${d.name} (${d.sample_count} 行)`,
                  value: d.id,
                }))}
              />
              <Button
                type="primary"
                icon={<FileTextOutlined />}
                loading={generating}
                disabled={!selectedDsId || hasDirectIds}
                onClick={handleGenerateDs}
              >
                生成分析
              </Button>
            </Space>

            {scanning && <Spin tip="正在扫描隐私风险..." />}

            {!scanning && hasDirectIds && (
              <Alert
                type="error"
                showIcon
                icon={<WarningOutlined />}
                message="检测到身份标识字段"
                description={
                  <>
                    <p>{privacySummary}</p>
                    <p>
                      请先在数据集详情页将这些字段角色设为「忽略」后再进行 AI 分析。
                      身份标识字段不应发送给外部 AI 模型。
                    </p>
                    <List
                      size="small"
                      dataSource={highRiskFields}
                      renderItem={(item) => (
                        <List.Item>
                          <Tag color="red">{CLASS_LABELS[item.classification]}</Tag>
                          {item.field} — {item.reason}
                        </List.Item>
                      )}
                    />
                  </>
                }
                style={{ marginTop: 12 }}
              />
            )}

            {!scanning && !hasDirectIds && privacyFields.length > 0 && mediumRiskFields.length > 0 && (
              <Alert
                type="warning"
                showIcon
                message="隐私提示"
                description={
                  <>
                    <p>{privacySummary}</p>
                    <List
                      size="small"
                      dataSource={mediumRiskFields}
                      renderItem={(item) => (
                        <List.Item>
                          <Tag color={RISK_COLORS[item.risk_level]}>
                            {CLASS_LABELS[item.classification]}
                          </Tag>
                          {item.field} — {item.reason}
                        </List.Item>
                      )}
                    />
                  </>
                }
                style={{ marginTop: 12 }}
              />
            )}

            {!scanning && !hasDirectIds && privacyFields.length > 0 && mediumRiskFields.length === 0 && (
              <Alert
                type="success"
                showIcon
                message="隐私扫描通过 — 未检测到高风险字段"
                style={{ marginTop: 12 }}
              />
            )}

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
