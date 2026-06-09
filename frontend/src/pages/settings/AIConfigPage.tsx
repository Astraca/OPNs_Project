import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  StarFilled,
  StarOutlined,
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
  api_key: string;
  api_key_full: string;
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

const TEMPLATE_TYPE_LABELS: Record<string, string> = {
  dataset_analysis: "数据集分析",
  model_analysis: "模型分析",
  prediction_explanation: "预测说明",
};

export default function AIConfigPage() {
  const [providers, setProviders] = useState<Record<string, AIProvider>>({});
  const [configs, setConfigs] = useState<AIConfigItem[]>([]);
  const [templates, setTemplates] = useState<PromptTemplateItem[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<AIConfigItem | null>(null);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);

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
    form.setFieldsValue({ is_active: configs.length === 0 });
    setModalOpen(true);
  }

  function openEdit(cfg: AIConfigItem) {
    setEditingConfig(cfg);
    form.setFieldsValue({
      name: cfg.name,
      provider: cfg.provider,
      api_base: cfg.api_base,
      api_key: cfg.api_key_full,
      model_name: cfg.model_name,
      is_active: cfg.is_active,
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
      if (editingConfig) {
        await request.put(`/ai-config/configs/${editingConfig.id}`, values);
        message.success("配置已更新");
      } else {
        await request.post("/ai-config/configs", values);
        message.success("配置已创建");
      }
      setModalOpen(false);
      await loadData();
    } catch {
      message.error("保存失败");
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

  async function handleSetActive(id: number) {
    try {
      await request.put(`/ai-config/configs/${id}`, { is_active: true });
      await loadData();
    } catch {
      message.error("设置失败");
    }
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
    { title: "API Key", dataIndex: "api_key", ellipsis: true },
    {
      title: "状态",
      dataIndex: "is_active",
      render: (v: boolean, record) =>
        v ? (
          <Tag color="green" icon={<StarFilled />}>启用中</Tag>
        ) : (
          <Button size="small" icon={<StarOutlined />} onClick={() => handleSetActive(record.id)}>
            启用
          </Button>
        ),
    },
    {
      title: "操作",
      render: (_, record) => (
        <Space>
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
                <Table rowKey="id" columns={configColumns} dataSource={configs} pagination={false} />
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
            <Input placeholder="https://api.deepseek.com/v1" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={[{ required: true }]}>
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item name="model_name" label="模型名称" rules={[{ required: true }]}>
            <Input placeholder="deepseek-chat" />
          </Form.Item>
          <Form.Item name="is_active" label="设为默认" valuePropName="checked">
            <Switch />
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
          <Form.Item name="system_prompt" label="系统提示词">
            <Input.TextArea rows={3} placeholder="设定 AI 的角色和行为" />
          </Form.Item>
          <Form.Item
            name="user_prompt"
            label="用户提示词"
            rules={[{ required: true }]}
            extra="可用变量：{sample_count}, {feature_count}, {target_columns}, {algorithm}, {metrics}, {job_type} 等"
          >
            <Input.TextArea rows={5} placeholder="包含 {variable} 占位符的模板" />
          </Form.Item>
        </Form>
      </Modal>
    </main>
  );
}
