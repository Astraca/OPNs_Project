import { ArrowLeftOutlined } from "@ant-design/icons";
import { Alert, Button, Form, Input, Typography, message } from "antd";
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
      message.success("数据集已创建，请上传数据文件并在「数据信息」中设置任务类型和说明");
      navigate(`/datasets/${dataset.id}`);
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      message.error(typeof detail === "string" ? detail : "创建数据集失败");
    }
  }

  return (
    <main>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>新建数据集</Typography.Title>
        <Button
          icon={<ArrowLeftOutlined />}
          style={{ borderColor: "#1677ff", color: "#1677ff" }}
          onClick={() => navigate("/datasets")}
        >
          返回
        </Button>
      </div>
      <Form
        form={form}
        layout="vertical"
        className="dataset-form"
        onFinish={handleSubmit}
      >
        <Form.Item name="name" label="数据集名称" rules={[{ required: true, message: "请输入数据集名称" }]}>
          <Input maxLength={128} placeholder="例如：IgAN 病理数据集、CKD 临床数据" />
        </Form.Item>
        <Alert
          type="info"
          showIcon
          message="创建后请上传文件"
          description="创建数据集后，您需要上传数据文件。任务类型和说明可在「数据信息」页面中设置，字段含义等 AI 辅助信息也可在同一页面中填写。支持 CSV、XLSX 格式，最大 10 MB。"
          style={{ marginBottom: 16 }}
        />
        <div style={{ textAlign: "center" }}>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            style={{ borderRadius: 24, padding: "0 48px", height: 48, fontSize: 16 }}
          >
            创建数据集
          </Button>
        </div>
      </Form>
    </main>
  );
}
