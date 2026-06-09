import { InboxOutlined } from "@ant-design/icons";
import { Alert, Form, Select, Table, Typography, Upload, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { UploadProps } from "antd";
import { useEffect, useMemo, useState } from "react";

import { listModels } from "../../api/models";
import { runBatchRegressionPrediction } from "../../api/predictions";
import type { MLModel } from "../../types/model";
import type { BatchPredictionResponse } from "../../types/prediction";
import "./PredictionPages.css";


const { Dragger } = Upload;

export default function RegressionBatchPredictionPage() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [modelId, setModelId] = useState<number | null>(null);
  const [result, setResult] = useState<BatchPredictionResponse | null>(null);

  useEffect(() => {
    async function loadModels() {
      try {
        const allModels = await listModels();
        setModels(allModels.filter((m) => m.task_type === "regression"));
      } catch {
        message.error("模型列表加载失败");
      }
    }
    void loadModels();
  }, []);

  const uploadProps: UploadProps = {
    accept: ".csv,.xlsx,.txt,.dat,.data",
    showUploadList: false,
    beforeUpload: async (file) => {
      if (!modelId) {
        message.warning("请先选择回归模型");
        return false;
      }
      try {
        setResult(await runBatchRegressionPrediction(modelId, file));
        message.success("批量回归预测完成");
      } catch {
        message.error("批量预测失败，请检查文件字段是否与模型一致");
      }
      return false;
    },
  };

  const columns: ColumnsType<Record<string, unknown>> = useMemo(() => {
    const first = result?.rows[0];
    if (!first) return [];
    return Object.keys(first).map((key) => ({
      title: key,
      dataIndex: key,
      ellipsis: true,
      render: (value: unknown) => (typeof value === "number" ? value.toFixed(4) : String(value ?? "")),
    }));
  }, [result?.rows]);

  const rows = useMemo(
    () => (result?.rows ?? []).map((row, index) => ({ ...row, __row_id: index })),
    [result?.rows],
  );

  return (
    <main>
      <Typography.Title level={3}>回归批量预测</Typography.Title>
      <section className="prediction-form">
        <Form layout="vertical">
          <Form.Item label="回归模型" required>
            <Select
              placeholder={models.length ? "选择模型" : "暂无回归模型"}
              options={models.map((m) => ({ label: `${m.model_name} (${m.algorithm})`, value: m.id }))}
              onChange={(value: number) => setModelId(value)}
            />
          </Form.Item>
        </Form>
        <Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">上传 CSV 或 XLSX 文件进行批量回归预测</p>
          <p className="ant-upload-hint">文件字段需包含模型训练时使用的输入特征。</p>
        </Dragger>
      </section>
      {result && (
        <section className="prediction-section">
          <Typography.Title level={4}>预测结果</Typography.Title>
          <Alert type="info" showIcon message={result.disclaimer} />
          <Table rowKey="__row_id" columns={columns} dataSource={rows} scroll={{ x: true }} />
        </section>
      )}
    </main>
  );
}
