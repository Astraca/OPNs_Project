import { BulbOutlined, SyncOutlined } from "@ant-design/icons";
import { Alert, Button, Form, Input, InputNumber, Modal, Select, Slider, Space, Typography, message } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listDatasets } from "../../api/datasets";
import { generateTrainingSuggestions } from "../../api/ai";
import { trainModel, trainRegressionModel } from "../../api/models";
import type { Dataset } from "../../types/dataset";
import type { AIAnalysisReport } from "../../types/ai";
import type { ModelAlgorithm, ModelTrainPayload, RegressionTrainPayload } from "../../types/model";
import AIReportPanel from "../ai/AIReportPanel";
import "./ModelPages.css";


type TaskMode = "multi_output_classification" | "classification" | "regression";

function isOpnsAlgorithm(algo: ModelAlgorithm | undefined): boolean {
  return (algo ?? "").startsWith("OPNs");
}

const MODE_LABELS: Record<TaskMode, string> = {
  multi_output_classification: "多标签分类（如 IgAN M/E/S/T/C）",
  classification: "单标签分类（如患病/健康）",
  regression: "回归预测（如 eGFR、血压值）",
};

function defaultAlgorithm(mode: TaskMode): ModelAlgorithm {
  if (mode === "regression") return "OPNs-SVR";
  return "OPNs-SVM";
}

// ── Bidirectional test-size input ─────────────────────────────────────────

function TestSizeInput({ value = 0.2, onChange }: { value?: number; onChange?: (v: number) => void }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <Slider
        min={0.1} max={0.4} step={0.05}
        marks={{ 0.1: "10%", 0.2: "20%", 0.3: "30%", 0.4: "40%" }}
        value={value} onChange={(v) => onChange?.(v as number)}
        style={{ flex: 1 }}
      />
      <InputNumber
        min={0.1} max={0.4} step={0.05} value={value}
        onChange={(v) => {
          if (v != null) {
            if (v < 0.1 || v > 0.4) message.warning("测试集比例合法区间为 0.1 ~ 0.4");
            onChange?.(Math.min(0.4, Math.max(0.1, v)));
          }
        }}
        style={{ width: 72 }}
      />
    </div>
  );
}

export default function ModelTrainPage() {
  const navigate = useNavigate();
  const [form] = Form.useForm<ModelTrainPayload | RegressionTrainPayload>();
  const [allDatasets, setAllDatasets] = useState<Dataset[]>([]);
  const [training, setTraining] = useState(false);
  const [mode, setMode] = useState<TaskMode>("multi_output_classification");
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<ModelAlgorithm>("OPNs-SVM");
  const [aiSuggesting, setAiSuggesting] = useState(false);
  const [aiReport, setAiReport] = useState<AIAnalysisReport | null>(null);
  const [aiModalOpen, setAiModalOpen] = useState(false);

  const datasets = useMemo(
    () => allDatasets.filter((d) => d.file_path && d.task_type === mode),
    [allDatasets, mode],
  );

  useEffect(() => {
    (async () => { try { setAllDatasets(await listDatasets()); } catch { message.error("数据集加载失败"); } })();
  }, []);

  const selectedDataset = useMemo(
    () => datasets.find((d) => d.id === selectedDatasetId) ?? null,
    [datasets, selectedDatasetId],
  );

  function handleDatasetChange(datasetId: number | undefined) {
    setSelectedDatasetId(datasetId ?? null);
    if (datasetId == null) {
      form.resetFields(["target_columns", "target_column"]);
      return;
    }
    const ds = datasets.find((d) => d.id === datasetId);
    if (!ds?.target_columns.length) return;
    if (mode === "regression") {
      form.setFieldsValue({ target_column: ds.target_columns[0] } as Partial<RegressionTrainPayload>);
    } else {
      form.setFieldsValue({ target_columns: ds.target_columns } as Partial<ModelTrainPayload>);
    }
  }

  function handleModeChange(value: TaskMode) {
    setMode(value);
    const algo = defaultAlgorithm(value);
    setSelectedAlgorithm(algo);
    setSelectedDatasetId(null);
    form.resetFields(["dataset_id", "algorithm", "target_columns", "target_column", "pairing_method"]);
    form.setFieldsValue({ algorithm: algo, pairing_method: "adjacent" });
  }

  const isClassification = mode === "multi_output_classification" || mode === "classification";

  async function handleSubmit(values: ModelTrainPayload | RegressionTrainPayload) {
    setTraining(true);
    try {
      if (mode === "regression") {
        const model = await trainRegressionModel(values as RegressionTrainPayload);
        message.success("回归模型训练完成");
        navigate(`/models/${model.id}/evaluation`);
      } else {
        const payload = { ...values as ModelTrainPayload, task_type: mode };
        const model = await trainModel(payload);
        message.success("模型训练完成");
        navigate(`/models/${model.id}/evaluation`);
      }
    } catch (err: unknown) {
      const detail = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail : undefined;
      message.error(typeof detail === "string" ? detail : mode === "regression"
        ? "回归模型训练失败" : "模型训练失败");
    } finally { setTraining(false); }
  }

  async function handleTrainingSuggestion() {
    if (!selectedDatasetId) {
      message.warning("请先选择数据集");
      return;
    }
    setAiSuggesting(true);
    try {
      const report = await generateTrainingSuggestions(selectedDatasetId);
      setAiReport(report);
      setAiModalOpen(true);
      message.success("AI 训练建议已生成");
    } catch (err: unknown) {
      const detail = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail : undefined;
      message.error(typeof detail === "string" ? detail : "AI 训练建议生成失败");
    } finally {
      setAiSuggesting(false);
    }
  }

  return (
    <main>
      <Typography.Title level={3}>训练模型</Typography.Title>
      <Form
        form={form} layout="vertical" className="model-form"
        initialValues={{ algorithm: "OPNs-SVM", pairing_method: "adjacent", test_size: 0.2, random_state: 42 }}
        onFinish={handleSubmit}
      >
        <Form.Item label="任务类型">
          <Select value={mode}
            options={Object.entries(MODE_LABELS).map(([k, v]) => ({ label: v, value: k }))}
            onChange={handleModeChange}
          />
        </Form.Item>

        <Form.Item name="dataset_id" label="数据集" rules={[{ required: true, message: "请选择数据集" }]}>
          <Select
            placeholder="请选择训练数据集"
            options={datasets.map((d) => ({
              label: `${d.name} (${d.sample_count} 行, 目标: ${d.target_columns.length ? d.target_columns.join(",") : "未设置"})`,
              value: d.id,
            }))}
            onChange={handleDatasetChange}
          />
        </Form.Item>

        {selectedDataset && !selectedDataset.target_columns.length && (
          <Alert type="warning" showIcon message="该数据集未设置目标字段"
            description="请先在数据集详情页设置目标字段，然后再来训练模型。"
            style={{ marginBottom: 16 }}
          />
        )}

        <Form.Item>
          <Button
            icon={<BulbOutlined />}
            loading={aiSuggesting}
            disabled={!selectedDatasetId}
            onClick={handleTrainingSuggestion}
          >
            AI 训练建议
          </Button>
        </Form.Item>

        <Form.Item name="model_name" label="模型名称" rules={[{ required: true, message: "请输入模型名称" }]}>
          <Input maxLength={128} placeholder="请输入模型名称" />
        </Form.Item>

        {isClassification && (
          <>
            <Form.Item name="algorithm" label="算法" rules={[{ required: true }]} initialValue="OPNs-SVM">
              <Select
                options={[
                  { label: "OPNs-SVM", value: "OPNs-SVM" },
                  { label: "标准 SVM", value: "SVM" },
                  { label: "随机森林 (分类)", value: "RandomForest" },
                  { label: "逻辑回归", value: "LogisticRegression" },
                ]}
                onChange={(v) => setSelectedAlgorithm(v)}
              />
            </Form.Item>
            <Form.Item name="target_columns" label="目标字段（可多选）"
              rules={[{ required: true, message: "请选择至少一个目标字段" }]}>
              <Select mode="multiple" placeholder="选择目标字段"
                options={selectedDataset ? selectedDataset.target_columns.map((t) => ({ label: t, value: t })) : []}
              />
            </Form.Item>
          </>
        )}

        {mode === "regression" && (
          <>
            <Form.Item name="algorithm" label="算法" rules={[{ required: true }]} initialValue="OPNs-SVR">
              <Select
                options={[
                  { label: "OPNs-SVR", value: "OPNs-SVR" },
                  { label: "标准 SVR", value: "SVR" },
                  { label: "随机森林 (回归)", value: "RandomForest" },
                  { label: "岭回归 (Ridge)", value: "Ridge" },
                ]}
                onChange={(v) => setSelectedAlgorithm(v)}
              />
            </Form.Item>
            <Form.Item name="target_column" label="目标字段（回归）"
              rules={[{ required: true, message: "请选择连续目标字段" }]}>
              <Select placeholder="选择目标字段"
                options={selectedDataset ? selectedDataset.target_columns.map((t) => ({ label: t, value: t })) : []}
              />
            </Form.Item>
          </>
        )}

        {isOpnsAlgorithm(selectedAlgorithm) && (
          <Form.Item name="pairing_method" label="OPNs 配对方式" rules={[{ required: true }]}>
            <Select options={[
              { label: "相邻配对", value: "adjacent" },
              { label: "随机配对", value: "random" },
              { label: "相关性贪心配对", value: "correlation_greedy" },
            ]} />
          </Form.Item>
        )}

        <Form.Item name="test_size" label="测试集比例" initialValue={0.2}
          rules={[{ required: true }, { validator: (_, v) => v >= 0.1 && v <= 0.4 ? Promise.resolve() : Promise.reject(new Error("测试集比例需在 0.1 ~ 0.4 之间")) }]}>
          <TestSizeInput />
        </Form.Item>

        <Form.Item label="随机种子">
          <Space.Compact>
            <Form.Item name="random_state" rules={[{ required: true }]} initialValue={42} noStyle>
              <InputNumber min={0} max={999999} style={{ width: 120 }} />
            </Form.Item>
            <Button icon={<SyncOutlined />} onClick={() => form.setFieldsValue({ random_state: Math.floor(Math.random() * 100000) })} title="随机生成种子" />
          </Space.Compact>
        </Form.Item>

        <Button type="primary" htmlType="submit" loading={training}>开始训练</Button>
      </Form>
      <Modal
        title="AI 训练建议"
        open={aiModalOpen}
        onCancel={() => setAiModalOpen(false)}
        footer={null}
        width={760}
      >
        <AIReportPanel report={aiReport} />
      </Modal>
    </main>
  );
}
