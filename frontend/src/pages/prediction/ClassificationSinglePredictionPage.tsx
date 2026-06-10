import { Alert, Button, Col, Form, InputNumber, Row, Select, Space, Statistic, Typography, message } from "antd";
import { useEffect, useMemo, useState } from "react";

import { listModels } from "../../api/models";
import { predictSingleIgan } from "../../api/predictions";
import type { MLModel } from "../../types/model";
import type { SinglePredictionResponse } from "../../types/prediction";
import { displayFieldName } from "../../utils/fieldNames";
import "./PredictionPages.css";


export default function ClassificationSinglePredictionPage() {
  const [form] = Form.useForm();
  const [models, setModels] = useState<MLModel[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [result, setResult] = useState<SinglePredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadModels() {
      try {
        const allModels = await listModels();
        setModels(allModels.filter((m) => m.task_type !== "regression"));
      } catch {
        message.error("模型列表加载失败");
      }
    }
    void loadModels();
  }, []);

  const selectedModel = useMemo(
    () => models.find((m) => m.id === selectedModelId) ?? null,
    [models, selectedModelId],
  );

  async function handleSubmit(values: Record<string, unknown>) {
    if (!selectedModelId || !selectedModel) {
      message.warning("请选择模型");
      return;
    }
    setLoading(true);
    try {
      const inputData = { ...values };
      delete inputData.model_id;
      setResult(await predictSingleIgan({ model_id: selectedModelId, input_data: inputData }));
      message.success("预测完成");
    } catch {
      message.error("预测失败，请检查输入字段");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <Typography.Title level={3}>分类单样本预测</Typography.Title>
      <Form form={form} layout="vertical" className="prediction-form" onFinish={handleSubmit}>
        <Form.Item name="model_id" label="分类模型" rules={[{ required: true }]}>
          <Select
            placeholder={models.length ? "请选择分类模型" : "暂无分类模型"}
            options={models.map((m) => ({ label: `${m.model_name} (${m.algorithm})`, value: m.id }))}
            onChange={(v: number) => setSelectedModelId(v)}
          />
        </Form.Item>
        {selectedModel && (
          <div className="prediction-features-scroll">
            <Row gutter={[12, 8]}>
              {selectedModel.feature_columns.map((feature) => (
                <Col xs={12} md={8} lg={6} key={feature}>
                  <Form.Item name={feature} label={displayFieldName(feature)} style={{ marginBottom: 8 }}>
                    <InputNumber style={{ width: "100%" }} placeholder="输入值" />
                  </Form.Item>
                </Col>
              ))}
            </Row>
          </div>
        )}
        <Space style={{ marginTop: 12 }}>
          <Button type="primary" htmlType="submit" loading={loading} disabled={!selectedModelId}>开始预测</Button>
          <Button onClick={() => { form.resetFields(); setResult(null); }}>清空</Button>
        </Space>
      </Form>

      {result && (
        <section className="prediction-section">
          <Typography.Title level={4}>预测结果</Typography.Title>
          <Row gutter={[16, 16]}>
            {Object.entries(result.result).map(([target, item]) => (
              <Col xs={24} md={8} key={target}>
                <Statistic title={target} value={item.label} suffix={item.probability ? `(${item.probability})` : ""} />
              </Col>
            ))}
          </Row>
          <Alert className="prediction-section" type="info" showIcon message={result.disclaimer} />
        </section>
      )}
    </main>
  );
}
