import { Alert, Button, Form, Input, Select, Typography, message } from "antd";
import { useNavigate } from "react-router-dom";

import { createDataset } from "../../api/datasets";
import type { DatasetCreatePayload } from "../../types/dataset";
import "./DatasetPages.css";


export default function DatasetCreatePage() {
  const navigate = useNavigate();
  const [form] = Form.useForm<DatasetCreatePayload>();

  async function handleSubmit(values: DatasetCreatePayload) {
    try {
      const dataset = await createDataset(values);
      message.success("数据集已创建，请上传数据文件并确认目标字段");
      navigate(`/datasets/${dataset.id}`);
    } catch {
      message.error("创建数据集失败");
    }
  }

  return (
    <main>
      <Typography.Title level={3}>新建数据集</Typography.Title>
      <Form
        form={form}
        layout="vertical"
        className="dataset-form"
        initialValues={{ task_type: "multi_output_classification" }}
        onFinish={handleSubmit}
      >
        <Form.Item name="name" label="数据集名称" rules={[{ required: true, message: "请输入数据集名称" }]}>
          <Input maxLength={128} placeholder="例如：IgAN 病理数据集、CKD 临床数据" />
        </Form.Item>
        <Form.Item name="task_type" label="任务类型" rules={[{ required: true }]}>
          <Select
            options={[
              { label: "多标签分类（如 IgAN M/E/S/T/C）", value: "multi_output_classification" },
              { label: "单标签分类（如患病/健康）", value: "classification" },
              { label: "回归预测（如 eGFR、血压值）", value: "regression" },
            ]}
          />
        </Form.Item>
        <Form.Item name="description" label="说明">
          <Input.TextArea rows={4} maxLength={2000} placeholder="可选：描述数据来源、字段含义等" />
        </Form.Item>
        <Alert
          type="info"
          showIcon
          message="支持的文件格式"
          description="CSV、XLSX、TXT、DAT、DATA。系统会自动检测分隔符（逗号、制表符、空格等）和表头。上传后请确认目标字段是否正确识别。"
          style={{ marginBottom: 16 }}
        />
        <Button type="primary" htmlType="submit">
          创建数据集
        </Button>
      </Form>
    </main>
  );
}
