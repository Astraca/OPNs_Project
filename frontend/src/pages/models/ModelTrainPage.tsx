import { SyncOutlined } from "@ant-design/icons";
import { Alert, Button, Form, Input, InputNumber, Select, Slider, Space, Typography, message } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listDatasets } from "../../api/datasets";
import { trainModel, trainRegressionModel } from "../../api/models";
import type { Dataset } from "../../types/dataset";
import type { ModelTrainPayload, RegressionTrainPayload } from "../../types/model";
import "./ModelPages.css";


type TaskMode = "classification" | "regression";

function isOpnsAlgorithm(algo: string | undefined): boolean {
  return (algo ?? "").startsWith("OPNs");
}

const CLASSIFICATION_TASK_TYPES = ["multi_output_classification", "classification"];
const REGRESSION_TASK_TYPES = ["regression"];

// ── Bidirectional test-size input (Slider ↔ InputNumber) ─────────────────

function TestSizeInput({ value = 0.2, onChange }: { value?: number; onChange?: (v: number) => void }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <Slider
        min={0.1}
        max={0.4}
        step={0.05}
        marks={{ 0.1: "10%", 0.2: "20%", 0.3: "30%", 0.4: "40%" }}
        value={value}
        onChange={(v) => onChange?.(v as number)}
        style={{ flex: 1 }}
      />
      <InputNumber
        min={0.1}
        max={0.4}
        step={0.05}
        value={value}
        onChange={(v) => {
          if (v != null) {
            if (v < 0.1 || v > 0.4) {
              message.warning("测试集比例合法区间为 0.1 ~ 0.4");
            }
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
  const [mode, setMode] = useState<TaskMode>("classification");
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>("OPNs-SVM");

  const datasets = useMemo(
    () => allDatasets.filter((d) => {
      const types = mode === "regression" ? REGRESSION_TASK_TYPES : CLASSIFICATION_TASK_TYPES;
      return d.file_path && types.includes(d.task_type);
    }),
    [allDatasets, mode],
  );

  useEffect(() => {
    async function loadDatasets() {
      try {
        setAllDatasets(await listDatasets());
      } catch {
        message.error("数据集加载失败");
      }
    }
    void loadDatasets();
  }, []);

  const selectedDataset = useMemo(
    () => datasets.find((d) => d.id === selectedDatasetId) ?? null,
    [datasets, selectedDatasetId],
  );

  // When dataset changes, auto-populate target fields
  function handleDatasetChange(datasetId: number) {
    setSelectedDatasetId(datasetId);
    const ds = datasets.find((d) => d.id === datasetId);
    if (!ds) return;

    if (mode === "classification" && ds.target_columns.length > 0) {
      form.setFieldsValue({ target_columns: ds.target_columns } as Partial<ModelTrainPayload>);
    } else if (mode === "regression" && ds.target_columns.length > 0) {
      form.setFieldsValue({ target_column: ds.target_columns[0] } as Partial<RegressionTrainPayload>);
    }
  }

  function handleModeChange(value: TaskMode) {
    setMode(value);
    const defaultAlgo = value === "regression" ? "OPNs-SVR" : "OPNs-SVM";
    setSelectedAlgorithm(defaultAlgo);
    form.resetFields(["algorithm", "target_columns", "target_column"]);
    form.setFieldsValue({ algorithm: defaultAlgo });
    if (selectedDataset) {
      if (value === "classification" && selectedDataset.target_columns.length > 0) {
        form.setFieldsValue({ target_columns: selectedDataset.target_columns } as Partial<ModelTrainPayload>);
      } else if (value === "regression" && selectedDataset.target_columns.length > 0) {
        form.setFieldsValue({ target_column: selectedDataset.target_columns[0] } as Partial<RegressionTrainPayload>);
      }
    }
  }

  async function handleSubmit(values: ModelTrainPayload | RegressionTrainPayload) {
    setTraining(true);
    try {
      if (mode === "regression") {
        const model = await trainRegressionModel(values as RegressionTrainPayload);
        message.success("回归模型训练完成");
        navigate(`/models/${model.id}/evaluation`);
      } else {
        const model = await trainModel(values as ModelTrainPayload);
        message.success("模型训练完成");
        navigate(`/models/${model.id}/evaluation`);
      }
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      message.error(typeof detail === "string" ? detail : mode === "regression"
        ? "回归模型训练失败，请检查数据集中是否包含连续目标变量和数值特征"
        : "模型训练失败，请检查数据集中是否包含目标列和数值特征");
    } finally {
      setTraining(false);
    }
  }

  return (
    <main>
      <Typography.Title level={3}>训练模型</Typography.Title>
      <Form
        form={form}
        layout="vertical"
        className="model-form"
        initialValues={{
          algorithm: "OPNs-SVM",
          pairing_method: "adjacent",
          test_size: 0.2,
          random_state: 42,
        }}
        onFinish={handleSubmit}
      >
        <Form.Item label="任务类型">
          <Select
            value={mode}
            options={[
              { label: "分类（多标签 / 单标签）", value: "classification" },
              { label: "回归预测", value: "regression" },
            ]}
            onChange={handleModeChange}
          />
        </Form.Item>

        <Form.Item name="dataset_id" label="数据集" rules={[{ required: true, message: "请选择数据集" }]}>
          <Select
            options={datasets.map((d) => ({
              label: `${d.name} (${d.sample_count} 行, 目标: ${d.target_columns.length ? d.target_columns.join(",") : "未设置"})`,
              value: d.id,
            }))}
            onChange={handleDatasetChange}
          />
        </Form.Item>

        {selectedDataset && !selectedDataset.target_columns.length && (
          <Alert
            type="warning"
            showIcon
            message="该数据集未设置目标字段"
            description="请先在数据集详情页设置目标字段（将目标列的 role 改为 target 并保存），然后再来训练模型。"
            style={{ marginBottom: 16 }}
          />
        )}

        <Form.Item name="model_name" label="模型名称" rules={[{ required: true, message: "请输入模型名称" }]}>
          <Input maxLength={128} />
        </Form.Item>

        {mode === "classification" && (
          <>
            <Form.Item name="algorithm" label="算法" rules={[{ required: true }]} initialValue="OPNs-SVM">
              <Select
                options={[
                  { label: "OPNs-SVM", value: "OPNs-SVM" },
                  { label: "标准 SVM", value: "SVM" },
                  { label: "随机森林 (分类)", value: "RandomForest" },
                  { label: "逻辑回归", value: "LogisticRegression" },
                ]}
                onChange={(value) => setSelectedAlgorithm(value)}
              />
            </Form.Item>
            <Form.Item
              name="target_columns"
              label="目标字段（可多选）"
              rules={[{ required: true, message: "请选择至少一个目标字段" }]}
            >
              <Select
                mode="multiple"
                placeholder="选择目标字段"
                options={
                  selectedDataset
                    ? selectedDataset.target_columns.map((t) => ({ label: t, value: t }))
                    : []
                }
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
                onChange={(value) => setSelectedAlgorithm(value)}
              />
            </Form.Item>
            <Form.Item
              name="target_column"
              label="目标字段（回归）"
              rules={[{ required: true, message: "请选择连续目标字段" }]}
            >
              <Select
                placeholder="选择目标字段"
                options={
                  selectedDataset
                    ? selectedDataset.target_columns.map((t) => ({ label: t, value: t }))
                    : []
                }
              />
            </Form.Item>
          </>
        )}

        {isOpnsAlgorithm(selectedAlgorithm) && (
          <Form.Item name="pairing_method" label="OPNs 配对方式" rules={[{ required: true }]}>
            <Select
              options={[
                { label: "相邻配对", value: "adjacent" },
                { label: "随机配对", value: "random" },
                { label: "相关性贪心配对", value: "correlation_greedy" },
              ]}
            />
          </Form.Item>
        )}

        <Form.Item
          name="test_size"
          label="测试集比例"
          initialValue={0.2}
          rules={[
            { required: true },
            {
              validator: (_, value) =>
                value >= 0.1 && value <= 0.4
                  ? Promise.resolve()
                  : Promise.reject(new Error("测试集比例需在 0.1 ~ 0.4 之间")),
            },
          ]}
        >
          <TestSizeInput />
        </Form.Item>

        <Form.Item label="随机种子" style={{ marginBottom: 0 }}>
          <Space.Compact>
            <Form.Item name="random_state" rules={[{ required: true }]} initialValue={42} noStyle>
              <InputNumber min={0} max={999999} style={{ width: 120 }} />
            </Form.Item>
            <Button
              icon={<SyncOutlined />}
              onClick={() => form.setFieldsValue({ random_state: Math.floor(Math.random() * 100000) })}
              title="随机生成种子"
            />
          </Space.Compact>
        </Form.Item>

        <Button type="primary" htmlType="submit" loading={training}>
          开始训练
        </Button>
      </Form>
    </main>
  );
}
