import { Button, Form, Input, Select, Typography, message } from "antd";
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
      message.success("数据集已创建");
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
          <Input maxLength={128} />
        </Form.Item>
        <Form.Item name="task_type" label="任务类型" rules={[{ required: true }]}>
          <Select
            options={[
              { label: "IgAN 多标签分类", value: "multi_output_classification" },
              { label: "分类", value: "classification" },
              { label: "回归", value: "regression" },
            ]}
          />
        </Form.Item>
        <Form.Item name="description" label="说明">
          <Input.TextArea rows={4} maxLength={2000} />
        </Form.Item>
        <Button type="primary" htmlType="submit">
          创建
        </Button>
      </Form>
    </main>
  );
}
