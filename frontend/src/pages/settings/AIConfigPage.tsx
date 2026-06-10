import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";

import { request } from "../../api/request";


type AIProvider = {
  key: string;
  name: string;
  api_base: string;
  default_model: string;
};

type AIConfigItem = {
  id: number;
  name: string;
  provider: string;
  api_base: string;
  has_api_key: boolean;
  model_name: string;
  is_active: boolean;
};

type PromptTemplateItem = {
  id: number;
  name: string;
  template_type: string;
  system_prompt: string;
  user_prompt: string;
};

type TestStatus = "success" | "error";

const TEMPLATE_TYPE_LABELS: Record<string, string> = {
  dataset_analysis: "数据集分析",
  model_analysis: "模型分析",
  prediction_explanation: "预测说明",
  dataset_role_suggestions: "字段角色建议",
  training_suggestions: "训练参数建议",
};

const TEMPLATE_TYPE_HELP: Record<string, string> = {
  dataset_analysis:
    "提交给 AI：样本数、字段数、目标字段、缺失值摘要、标签分布、数据集结构化摘要。可用变量：{sample_count}, {feature_count}, {target_columns}, {missing_values}, {target_distribution}, {dataset_context}。",
  model_analysis:
    "提交给 AI：模型名称、任务类型、算法、目标字段、特征摘要、超参数、核心指标、混淆矩阵/ROC AUC/残差摘要等结构化数值。不提交图像或模型文件。可用变量：{model_name}, {task_type}, {algorithm}, {target_columns}, {feature_count}, {feature_columns}, {hyperparameters}, {opns_enabled}, {pairing_method}, {avg_f1}, {metrics}, {evaluation_context}, {model_context}。",
  prediction_explanation:
    "提交给 AI：预测任务类型、样本数量、首条预测结果摘要。可用变量：{job_type}, {sample_count}, {prediction_summary}。",
  dataset_role_suggestions:
    "提交给 AI：字段名称、类型、当前角色、缺失率、唯一值数量、基础统计和规则建议。可用变量：{task_type}, {target_columns}, {column_summary}。",
  training_suggestions:
    "提交给 AI：数据集任务类型、样本量、字段角色统计、目标字段、高缺失字段和规则训练建议。可用变量：{dataset_context}。",
};

export default function AIConfigPage() {
  const [providers, setProviders] = useState<Record<string, AIProvider>>({});
  const [configs, setConfigs] = useState<AIConfigItem[]>([]);
  const [templates, setTemplates] = useState<PromptTemplateItem[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<AIConfigItem | null>(null);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [activeSavingId, setActiveSavingId] = useState<number | null>(null);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [testStatus, setTestStatus] = useState<Record<number, TestStatus>>({});

  // Template modal
  const [tmplModalOpen, setTmplModalOpen] = useState(false);
  const [editingTmpl, setEditingTmpl] = useState<PromptTemplateItem | null>(null);
  const [tmplForm] = Form.useForm();

  async function loadData() {
    try {
      const [prov, cfgs, tmpls] = await Promise.all([
        request.get("/ai-config/providers").then((r) => r.data.providers),
        request.get("/ai-config/configs").then((r) => r.data),
        request.get("/ai-config/templates").then((r) => r.data),
      ]);
      setProviders(prov);
      setConfigs(cfgs);
      setTemplates(tmpls);
    } catch {
      message.error("AI 配置加载失败");
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  function openCreate() {
    setEditingConfig(null);
    form.resetFields();
    setModalOpen(true);
  }

  function openEdit(cfg: AIConfigItem) {
    setEditingConfig(cfg);
    form.setFieldsValue({
      name: cfg.name,
      provider: cfg.provider,
      api_base: cfg.api_base,
      api_key: "",
      model_name: cfg.model_name,
    });
    setModalOpen(true);
  }

  function fillProvider(providerKey: string) {
    const preset = providers[providerKey];
    if (preset) {
      form.setFieldsValue({
        api_base: preset.api_base,
        model_name: preset.default_model,
      });
    }
  }

  async function handleSave(values: Record<string, unknown>) {
    setSaving(true);
    try {
      const payload = { ...values };
      if (editingConfig && typeof payload.api_key === "string" && payload.api_key.trim() === "") {
        delete payload.api_key;
      }
      let saved: AIConfigItem;
      if (editingConfig) {
        saved = (await request.put<AIConfigItem>(`/ai-config/configs/${editingConfig.id}`, payload)).data;
        message.success("配置已更新");
      } else {
        saved = (await request.post<AIConfigItem>("/ai-config/configs", payload)).data;
        message.success("配置已创建");
      }
      setModalOpen(false);
      await loadData();
      void runConfigTest(saved.id, true);
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      message.error(typeof detail === "string" ? detail : "保存或测试失败");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await request.delete(`/ai-config/configs/${id}`);
      message.success("已删除");
      await loadData();
    } catch {
      message.error("删除失败");
    }
  }

  async function handleSetActive(id: number, checked: boolean) {
    if (checked && testStatus[id] !== "success") {
      message.warning("请先测试配置，测试成功后才能设为默认");
      return;
    }
    setActiveSavingId(id);
    try {
      await request.put(`/ai-config/configs/${id}`, { is_active: checked });
      await loadData();
    } catch {
      message.error("设置失败");
    } finally {
      setActiveSavingId(null);
    }
  }

  async function testConfig(id: number) {
    const { data } = await request.post<{ ok: boolean; message: string }>(`/ai-config/configs/${id}/test`);
    setTestStatus((current) => ({ ...current, [id]: "success" }));
    return data;
  }

  async function runConfigTest(id: number, silentSuccess = false) {
    setTestingId(id);
    try {
      const data = await testConfig(id);
      if (!silentSuccess) {
        message.success(data.message || "AI 配置测试成功");
      }
    } catch (err: unknown) {
      setTestStatus((current) => ({ ...current, [id]: "error" }));
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      message.error(typeof detail === "string" ? detail : "AI 配置测试失败");
    } finally {
      setTestingId(null);
    }
  }

  async function handleTestConfig(id: number) {
    await runConfigTest(id);
  }

  // Template handlers
  function openTmplCreate() {
    setEditingTmpl(null);
    tmplForm.resetFields();
    setTmplModalOpen(true);
  }

  function openTmplEdit(tmpl: PromptTemplateItem) {
    setEditingTmpl(tmpl);
    tmplForm.setFieldsValue(tmpl);
    setTmplModalOpen(true);
  }

  async function handleTmplSave(values: Record<string, unknown>) {
    try {
      if (editingTmpl) {
        await request.put(`/ai-config/templates/${editingTmpl.id}`, values);
        message.success("模板已更新");
      } else {
        await request.post("/ai-config/templates", values);
        message.success("模板已创建");
      }
      setTmplModalOpen(false);
      await loadData();
    } catch {
      message.error("保存失败");
    }
  }

  async function handleTmplDelete(id: number) {
    try {
      await request.delete(`/ai-config/templates/${id}`);
      message.success("已删除");
      await loadData();
    } catch {
      message.error("删除失败");
    }
  }

  const configColumns: ColumnsType<AIConfigItem> = [
    { title: "名称", dataIndex: "name" },
    {
      title: "提供商",
      dataIndex: "provider",
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    { title: "模型", dataIndex: "model_name", ellipsis: true },
    {
      title: "API Key",
      dataIndex: "has_api_key",
      render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "已保存" : "未设置"}</Tag>,
    },
    {
      title: "默认",
      dataIndex: "is_active",
      render: (v: boolean, record) => (
        <Switch
          checked={v}
          disabled={!v && testStatus[record.id] !== "success"}
          loading={activeSavingId === record.id}
          onChange={(checked) => handleSetActive(record.id, checked)}
        />
      ),
    },
    {
      title: "操作",
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            style={{ width: 72 }}
            icon={
              testStatus[record.id] === "success" ? (
                <CheckCircleOutlined style={{ color: "#52c41a" }} />
              ) : testStatus[record.id] === "error" ? (
                <CloseCircleOutlined style={{ color: "#ff4d4f" }} />
              ) : (
                <CheckCircleOutlined style={{ color: "#8c8c8c" }} />
              )
            }
            loading={testingId === record.id}
            onClick={() => handleTestConfig(record.id)}
          >
            测试
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const tmplColumns: ColumnsType<PromptTemplateItem> = [
    { title: "名称", dataIndex: "name" },
    {
      title: "类型",
      dataIndex: "template_type",
      render: (v: string) => <Tag>{TEMPLATE_TYPE_LABELS[v] ?? v}</Tag>,
    },
    {
      title: "用户提示词",
      dataIndex: "user_prompt",
      ellipsis: true,
      render: (v: string) => v.slice(0, 80) + (v.length > 80 ? "…" : ""),
    },
    {
      title: "操作",
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openTmplEdit(record)} />
          <Popconfirm title="确定删除？" onConfirm={() => handleTmplDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <main>
      <Typography.Title level={3}>AI 模型配置</Typography.Title>

      <Tabs
        items={[
          {
            key: "providers",
            label: "模型配置",
            children: (
              <Card
                extra={
                  <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
                    添加配置
                  </Button>
                }
              >
                <Table
                  rowKey="id"
                  columns={configColumns}
                  dataSource={configs}
                  pagination={{ pageSize: 6, showSizeChanger: false }}
                  scroll={{ x: 820 }}
                />
              </Card>
            ),
          },
          {
            key: "templates",
            label: "提示词模板",
            children: (
              <Card
                extra={
                  <Button type="primary" icon={<PlusOutlined />} onClick={openTmplCreate}>
                    添加模板
                  </Button>
                }
              >
                <Table rowKey="id" columns={tmplColumns} dataSource={templates} pagination={false} />
              </Card>
            ),
          },
        ]}
      />

      {/* Config Modal */}
      <Modal
        title={editingConfig ? "编辑模型配置" : "添加模型配置"}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saving}
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Form.Item name="name" label="配置名称" rules={[{ required: true }]}>
            <Input placeholder="例如：DeepSeek V3" />
          </Form.Item>
          <Form.Item name="provider" label="提供商" rules={[{ required: true }]}>
            <Select
              onChange={fillProvider}
              options={[
                ...Object.entries(providers).map(([k, v]) => ({ label: v.name, value: k })),
              ]}
            />
          </Form.Item>
          <Form.Item name="api_base" label="API 地址" rules={[{ required: true }]}>
            <Input placeholder="https://api.deepseek.com" />
          </Form.Item>
          <Form.Item
            name="api_key"
            label="API Key"
            rules={editingConfig ? [] : [{ required: true, message: "请输入 API Key" }]}
            extra={editingConfig ? "留空则保持当前 API Key 不变" : undefined}
          >
            <Input.Password placeholder={editingConfig ? "留空不修改" : "sk-..."} />
          </Form.Item>
          <Form.Item name="model_name" label="模型名称" rules={[{ required: true }]}>
            <Input placeholder="deepseek-chat" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Template Modal */}
      <Modal
        title={editingTmpl ? "编辑提示词模板" : "添加提示词模板"}
        open={tmplModalOpen}
        onCancel={() => setTmplModalOpen(false)}
        onOk={() => tmplForm.submit()}
        width={640}
      >
        <Form form={tmplForm} layout="vertical" onFinish={handleTmplSave}>
          <Form.Item name="name" label="模板名称" rules={[{ required: true }]}>
            <Input placeholder="例如：自定义数据集分析" />
          </Form.Item>
          <Form.Item name="template_type" label="模板类型" rules={[{ required: true }]}>
            <Select
              options={Object.entries(TEMPLATE_TYPE_LABELS).map(([k, v]) => ({
                label: v,
                value: k,
              }))}
            />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.template_type !== cur.template_type}>
            {({ getFieldValue }) => {
              const type = getFieldValue("template_type") as string | undefined;
              return type ? (
                <Typography.Paragraph type="secondary">
                  {TEMPLATE_TYPE_HELP[type]}
                </Typography.Paragraph>
              ) : null;
            }}
          </Form.Item>
          <Form.Item name="system_prompt" label="系统提示词">
            <Input.TextArea rows={3} placeholder="设定 AI 的角色和行为" />
          </Form.Item>
          <Form.Item
            name="user_prompt"
            label="用户提示词"
            rules={[{ required: true }]}
            extra="变量使用 {variable_name} 格式；未知变量会原样保留，便于逐步调试模板。"
          >
            <Input.TextArea rows={5} placeholder="包含 {variable} 占位符的模板" />
          </Form.Item>
        </Form>
      </Modal>
    </main>
  );
}
