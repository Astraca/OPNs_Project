import { InboxOutlined } from "@ant-design/icons";
import { Alert, Form, Select, Spin, Table, Typography, Upload, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { UploadProps } from "antd";
import { useEffect, useMemo, useState } from "react";

import { listModels } from "../../api/models";
import { runBatchPrediction } from "../../api/predictions";
import type { MLModel } from "../../types/model";
import type { BatchPredictionResponse } from "../../types/prediction";
import "./PredictionPages.css";


const { Dragger } = Upload;

export default function BatchPredictionPage() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [modelId, setModelId] = useState<number | null>(null);
  const [result, setResult] = useState<BatchPredictionResponse | null>(null);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    async function loadModels() {
      try {
        setModels(await listModels());
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
        message.warning("请先选择模型");
        return false;
      }
      setPredicting(true);
      try {
        setResult(await runBatchPrediction(modelId, file));
        message.success("批量预测完成");
      } catch {
        message.error("批量预测失败，请检查文件字段是否与模型一致");
      } finally {
        setPredicting(false);
      }
      return false;
    },
  };

  const columns: ColumnsType<Record<string, unknown>> = useMemo(() => {
    const first = result?.rows[0];
    if (!first) {
      return [];
    }
    return Object.keys(first).map((key) => ({
      title: key,
      dataIndex: key,
      ellipsis: true,
      render: (value: unknown) => String(value ?? ""),
    }));
  }, [result?.rows]);

  const rows = useMemo(
    () => (result?.rows ?? []).map((row, index) => ({ ...row, __row_id: index })),
    [result?.rows],
  );

  return (
    <main>
      <Typography.Title level={3}>批量预测</Typography.Title>
      <section className="prediction-form">
        <Form layout="vertical">
          <Form.Item label="模型" required>
            <Select
              placeholder="请选择分类模型"
              options={models.map((model) => ({ label: `${model.model_name} (${model.algorithm})`, value: model.id }))}
              onChange={(value: number) => setModelId(value)}
            />
          </Form.Item>
        </Form>
        {predicting && (
          <div className="prediction-batch-spin">
            <Spin tip="正在预测中，请稍候..." size="large" />
          </div>
        )}
        <Dragger {...uploadProps} disabled={predicting}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">上传 CSV 或 XLSX 文件进行批量预测</p>
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
