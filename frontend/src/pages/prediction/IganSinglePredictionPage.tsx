import { ArrowLeftOutlined } from "@ant-design/icons";
import { Alert, Button, Col, Form, InputNumber, Row, Select, Statistic, Typography, message } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { listModels } from "../../api/models";
import { predictSingleIgan } from "../../api/predictions";
import type { MLModel } from "../../types/model";
import type { SinglePredictionResponse } from "../../types/prediction";
import { displayFieldName } from "../../utils/fieldNames";
import "./PredictionPages.css";


export default function IganSinglePredictionPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fromModelId = searchParams.get("modelId");
  const [form] = Form.useForm();
  const [models, setModels] = useState<MLModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [result, setResult] = useState<SinglePredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadModels() {
      setModelsLoading(true);
      try {
        const all = await listModels();
        setModels(all.filter((m) => m.task_type !== "regression"));
      } catch {
        message.error("模型列表加载失败");
      } finally {
        setModelsLoading(false);
      }
    }

    void loadModels();
    // Auto-select model from query param
    const qModelId = Number(fromModelId);
    if (qModelId) {
      setSelectedModelId(qModelId);
      form.setFieldsValue({ model_id: qModelId });
    }
  }, [fromModelId, form]);

  const selectedModel = useMemo(
    () => models.find((model) => model.id === selectedModelId) ?? null,
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>IgAN 单病例预测</Typography.Title>
        {fromModelId && (
          <Button
            icon={<ArrowLeftOutlined />}
            style={{ borderColor: "#1677ff", color: "#1677ff" }}
            onClick={() => navigate(`/models/${fromModelId}`)}
          >
            返回
          </Button>
        )}
      </div>
      <Form form={form} layout="vertical" className="prediction-form" onFinish={handleSubmit}>
        <Form.Item name="model_id" label="模型" rules={[{ required: true, message: "请选择模型" }]}>
          <Select
            loading={modelsLoading}
            placeholder="请选择分类模型"
            options={models.map((model) => ({ label: `${model.model_name} (${model.algorithm})`, value: model.id }))}
            onChange={(value: number) => { setSelectedModelId(value); setResult(null); }}
          />
        </Form.Item>
        {selectedModel && (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <Typography.Text type="secondary">输入特征值</Typography.Text>
              <Button size="small" onClick={() => { form.resetFields(selectedModel?.feature_columns ?? []); setResult(null); }}>清空</Button>
            </div>
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
          </>
        )}
        <Button type="primary" htmlType="submit" loading={loading} disabled={!selectedModelId} style={{ marginTop: 12 }}>
          开始预测
        </Button>
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
