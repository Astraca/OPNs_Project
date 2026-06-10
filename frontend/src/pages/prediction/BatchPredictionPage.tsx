import { InboxOutlined } from "@ant-design/icons";
import { Alert, Button, Form, Select, Space, Spin, Table, Tag, Typography, Upload, message } from "antd";
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
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [result, setResult] = useState<BatchPredictionResponse | null>(null);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    (async () => { try { setModels(await listModels()); } catch { message.error("模型列表加载失败"); } })();
  }, []);

  const uploadProps: UploadProps = {
    accept: ".csv,.xlsx,.txt,.dat,.data",
    showUploadList: false,
    beforeUpload: (file) => {
      if (!modelId) { message.warning("请先选择模型"); return false; }
      setPendingFile(file);
      setResult(null);
      message.success(`已选择文件：${file.name}`);
      return false;
    },
  };

  async function handleStartPredict() {
    if (!modelId || !pendingFile) return;
    setPredicting(true);
    try {
      setResult(await runBatchPrediction(modelId, pendingFile));
      message.success("批量预测完成");
    } catch {
      message.error("批量预测失败，请检查文件字段是否与模型一致");
    } finally { setPredicting(false); }
  }

  const columns: ColumnsType<Record<string, unknown>> = useMemo(() => {
    const first = result?.rows[0];
    if (!first) return [];
    return Object.keys(first).map((key) => ({
      title: key, dataIndex: key, ellipsis: true,
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
              options={models.map((m) => ({ label: `${m.model_name} (${m.algorithm})`, value: m.id }))}
              onChange={(v: number) => { setModelId(v); setPendingFile(null); setResult(null); }}
            />
          </Form.Item>
        </Form>

        {!pendingFile ? (
          <Dragger {...uploadProps} disabled={!modelId}>
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">
              {modelId ? "点击或拖拽文件到此区域" : "请先选择模型"}
            </p>
            <p className="ant-upload-hint">支持 CSV / XLSX / TXT / DAT / DATA 格式</p>
          </Dragger>
        ) : (
          <div style={{ padding: 16, background: "#f6ffed", borderRadius: 8, border: "1px solid #b7eb8f" }}>
            <Space>
              <Tag color="green">{pendingFile.name}</Tag>
              <Button type="primary" loading={predicting} onClick={handleStartPredict}>
                开始预测
              </Button>
              <Upload {...uploadProps}><Button>重新选择文件</Button></Upload>
            </Space>
          </div>
        )}

        {predicting && (
          <div className="prediction-batch-spin">
            <Spin tip="正在预测中，请稍候..." size="large" />
          </div>
        )}
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
