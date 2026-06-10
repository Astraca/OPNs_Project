import { ArrowLeftOutlined, InfoCircleOutlined, SaveOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Select,
  Space,
  Spin,
  Typography,
  message,
} from "antd";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getDataset,
  updateDataset,
  getDatasetContext as fetchContext,
  saveDatasetContext,
  updateDatasetContext,
} from "../../api/datasets";
import type {
  Dataset,
  DatasetContext,
  DatasetContextPayload,
  DatasetTaskType,
} from "../../types/dataset";
import { displayFieldName } from "../../utils/fieldNames";


export default function DatasetContextPage() {
  const { id } = useParams();
  const datasetId = Number(id);
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [context, setContext] = useState<DatasetContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const ds = await getDataset(datasetId);
      setDataset(ds);
      // Seed form with base dataset info
      form.setFieldsValue({
        name: ds.name,
        task_type: ds.task_type,
        description: ds.description ?? "",
      });
      try {
        const ctx = await fetchContext(datasetId);
        setContext(ctx);
        form.setFieldsValue({
          name: ds.name,
          task_type: ds.task_type,
          description: ds.description ?? "",
          dataset_source: ctx.dataset_source ?? "",
          scenario_description: ctx.scenario_description ?? "",
          inclusion_criteria: ctx.inclusion_criteria ?? "",
          exclusion_criteria: ctx.exclusion_criteria ?? "",
          feature_descriptions: JSON.stringify(ctx.feature_descriptions ?? {}, null, 2),
          target_descriptions: JSON.stringify(ctx.target_descriptions ?? {}, null, 2),
          usage_notes: ctx.usage_notes ?? "",
        });
      } catch {
        setContext(null);
      }
    } catch {
      message.error("数据集加载失败");
    } finally {
      setLoading(false);
    }
  }, [datasetId, form]);

  useEffect(() => {
    if (Number.isFinite(datasetId)) void loadData();
  }, [datasetId, loadData]);

  async function handleSave(values: Record<string, unknown>) {
    setSaving(true);
    try {
      // Save base dataset info (name, task_type, description)
      const dsPayload = {
        name: String(values.name ?? ""),
        task_type: values.task_type as DatasetTaskType,
        description: String(values.description ?? ""),
      };
      const updatedDs = await updateDataset(datasetId, dsPayload);
      setDataset(updatedDs);

      // Parse JSON fields from TextArea strings
      let featureDescs: Record<string, string> = {};
      let targetDescs: Record<string, string> = {};
      try {
        const rawFeat = String(values.feature_descriptions ?? "").trim();
        if (rawFeat) featureDescs = JSON.parse(rawFeat);
      } catch { /* keep empty */ }
      try {
        const rawTarg = String(values.target_descriptions ?? "").trim();
        if (rawTarg) targetDescs = JSON.parse(rawTarg);
      } catch { /* keep empty */ }

      // Save extended context
      const ctxPayload: DatasetContextPayload = {
        dataset_source: String(values.dataset_source ?? "").trim() || null,
        scenario_description: String(values.scenario_description ?? "").trim() || null,
        inclusion_criteria: String(values.inclusion_criteria ?? "").trim() || null,
        exclusion_criteria: String(values.exclusion_criteria ?? "").trim() || null,
        feature_descriptions: featureDescs,
        target_descriptions: targetDescs,
        usage_notes: String(values.usage_notes ?? "").trim() || null,
      };
      const saved = context
        ? await updateDatasetContext(datasetId, ctxPayload)
        : await saveDatasetContext(datasetId, ctxPayload);
      setContext(saved);
      message.success("数据集信息已保存");
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      message.error(typeof detail === "string" ? detail : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <Spin size="large" />
      </main>
    );
  }

  if (!dataset) {
    return (
      <main>
        <Alert type="error" message="数据集不存在或无权访问" />
      </main>
    );
  }

  const targets = dataset.target_columns ?? [];

  return (
    <main>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Typography.Title level={3} style={{ margin: 0 }}>
            {dataset.name} — 数据信息
          </Typography.Title>
          <Button
            icon={<ArrowLeftOutlined />}
            style={{ borderColor: "#1677ff", color: "#1677ff" }}
            onClick={() => navigate(`/datasets/${datasetId}`)}
          >
            返回
          </Button>
        </div>

        <Alert
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
          message="填写数据信息有助于 AI 进行更准确的分析"
          description="您提供的任务类型、数据集来源、字段含义和目标变量说明将被 AI 用于生成更贴合实际场景的分析结果。"
        />

        <Card>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSave}
          >
            <Typography.Title level={5}>基本信息</Typography.Title>

            <Form.Item
              name="name"
              label="数据集名称"
              rules={[{ required: true, message: "请输入数据集名称" }]}
            >
              <Input maxLength={128} placeholder="例如：IgAN 病理数据集" />
            </Form.Item>

            <Form.Item
              name="task_type"
              label="任务类型"
              rules={[{ required: true, message: "请选择任务类型" }]}
            >
              <Select
                options={[
                  { label: "多标签分类（如 IgAN M/E/S/T/C）", value: "multi_output_classification" },
                  { label: "单标签分类（如患病/健康）", value: "classification" },
                  { label: "回归预测（如 eGFR、血压值）", value: "regression" },
                ]}
              />
            </Form.Item>

            <Form.Item name="description" label="说明">
              <Input.TextArea
                rows={3}
                maxLength={2000}
                placeholder="可选：描述数据来源、字段含义等"
              />
            </Form.Item>

            <Typography.Title level={5}>数据背景</Typography.Title>

            <Form.Item
              name="dataset_source"
              label="数据集来源"
              extra="例如：某院 IgA 肾病患者回顾性数据、公开数据库等"
            >
              <Input.TextArea
                rows={2}
                maxLength={2000}
                placeholder="描述数据集的来源和采集背景"
              />
            </Form.Item>

            <Form.Item
              name="scenario_description"
              label="应用场景说明"
              extra="例如：根据临床指标预测 IgAN 病理 MEST-C 标签"
            >
              <Input.TextArea
                rows={2}
                maxLength={2000}
                placeholder="说明该数据集在本系统中的研究用途"
              />
            </Form.Item>

            <Space size="large" style={{ width: "100%" }}>
              <Form.Item
                name="inclusion_criteria"
                label="入组标准"
                style={{ flex: 1 }}
              >
                <Input.TextArea rows={2} maxLength={2000} placeholder="例如：经肾活检确诊的 IgAN 患者" />
              </Form.Item>
              <Form.Item
                name="exclusion_criteria"
                label="排除标准"
                style={{ flex: 1 }}
              >
                <Input.TextArea rows={2} maxLength={2000} placeholder="例如：合并其他系统性疾病" />
              </Form.Item>
            </Space>

            <Typography.Title level={5}>字段含义</Typography.Title>
            <Form.Item
              name="feature_descriptions"
              label="特征字段说明"
              extra={`以 JSON 对象形式填写字段含义，如 ${'{ "egfr": "估算肾小球滤过率" }'}`}
            >
              <Input.TextArea
                rows={4}
                maxLength={5000}
                placeholder='{"egfr": "估算肾小球滤过率，反映肾功能水平", "proteinuria": "尿蛋白水平"}'
              />
            </Form.Item>

            <Form.Item
              name="target_descriptions"
              label="目标变量说明"
              extra="填写各目标标签的医学含义"
            >
              <Input.TextArea
                rows={4}
                maxLength={5000}
                placeholder={
                  targets.length
                    ? JSON.stringify(
                        Object.fromEntries(targets.map((t) => [displayFieldName(t), ""])),
                        null,
                        2,
                      )
                    : '{"M": "系膜细胞增生", "E": "毛细血管内增生"}'
                }
              />
            </Form.Item>

            <Form.Item
              name="usage_notes"
              label="使用注意事项"
            >
              <Input.TextArea
                rows={2}
                maxLength={2000}
                placeholder="数据使用限制、授权范围等"
              />
            </Form.Item>

            <Button
              type="primary"
              icon={<SaveOutlined />}
              htmlType="submit"
              loading={saving}
            >
              保存
            </Button>
          </Form>
        </Card>
      </Space>
    </main>
  );
}
