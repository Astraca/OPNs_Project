import { Button, Form, Input, InputNumber, Select, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listDatasets } from "../../api/datasets";
import { trainModel, trainRegressionModel } from "../../api/models";
import type { Dataset } from "../../types/dataset";
import type { ModelTrainPayload, RegressionTrainPayload } from "../../types/model";
import "./ModelPages.css";


type TaskMode = "classification" | "regression";

export default function ModelTrainPage() {
  const navigate = useNavigate();
  const [form] = Form.useForm<ModelTrainPayload | RegressionTrainPayload>();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [training, setTraining] = useState(false);
  const [mode, setMode] = useState<TaskMode>("classification");

  useEffect(() => {
    async function loadDatasets() {
      try {
        setDatasets((await listDatasets()).filter((d) => Boolean(d.file_path)));
      } catch {
        message.error("数据集加载失败");
      }
    }
    void loadDatasets();
  }, []);

  async function handleSubmit(values: ModelTrainPayload | RegressionTrainPayload) {
    setTraining(true);
    try {
      if (mode === "regression") {
        const model = await trainRegressionModel(values as RegressionTrainPayload);
        message.success("回归模型训练完成");
        navigate(`/models/${model.id}/evaluation`);
      } else {
        const model = await trainModel(values as ModelTrainPayload);
        message.success("模型训练完成");
        navigate(`/models/${model.id}/evaluation`);
      }
    } catch {
      message.error(mode === "regression"
        ? "回归模型训练失败，请检查数据集中是否包含连续目标变量和数值特征"
        : "模型训练失败，请检查数据集中是否包含 M/E/S/T/C 和数值特征");
    } finally {
      setTraining(false);
    }
  }

  return (
    <main>
      <Typography.Title level={3}>训练模型</Typography.Title>
      <Form
        form={form}
        layout="vertical"
        className="model-form"
        initialValues={{
          algorithm: "OPNs-SVM",
          target_columns: ["out-M", "out-E", "out-S", "out-T", "out-C"],
          pairing_method: "adjacent",
          test_size: 0.2,
          random_state: 42,
        }}
        onFinish={handleSubmit}
      >
        <Form.Item label="任务类型">
          <Select
            value={mode}
            options={[
              { label: "IgAN MEST-C 分类", value: "classification" },
              { label: "回归预测", value: "regression" },
            ]}
            onChange={(value: TaskMode) => {
              setMode(value);
              form.resetFields(["algorithm", "target_columns", "target_column"]);
            }}
          />
        </Form.Item>

        <Form.Item name="dataset_id" label="数据集" rules={[{ required: true, message: "请选择数据集" }]}>
          <Select
            options={datasets.map((d) => ({ label: `${d.name} (${d.sample_count} 行)`, value: d.id }))}
          />
        </Form.Item>

        <Form.Item name="model_name" label="模型名称" rules={[{ required: true, message: "请输入模型名称" }]}>
          <Input maxLength={128} />
        </Form.Item>

        {mode === "classification" && (
          <>
            <Form.Item name="algorithm" label="算法" rules={[{ required: true }]} initialValue="OPNs-SVM">
              <Select
                options={[
                  { label: "OPNs-SVM", value: "OPNs-SVM" },
                  { label: "标准 SVM", value: "SVM" },
                ]}
              />
            </Form.Item>
            <Form.Item
              name="target_columns"
              label="目标字段"
              rules={[{ required: true }]}
              initialValue={["out-M", "out-E", "out-S", "out-T", "out-C"]}
            >
              <Select
                mode="multiple"
                options={["out-M", "out-E", "out-S", "out-T", "out-C"].map((t) => ({ label: t, value: t }))}
              />
            </Form.Item>
          </>
        )}

        {mode === "regression" && (
          <>
            <Form.Item name="algorithm" label="算法" rules={[{ required: true }]} initialValue="OPNs-SVR">
              <Select
                options={[
                  { label: "OPNs-SVR", value: "OPNs-SVR" },
                  { label: "标准 SVR", value: "SVR" },
                ]}
              />
            </Form.Item>
            <Form.Item
              name="target_column"
              label="目标字段（回归）"
              rules={[{ required: true, message: "请输入连续目标字段名" }]}
            >
              <Input placeholder="例如：in-eGFR" maxLength={128} />
            </Form.Item>
          </>
        )}

        <Form.Item name="pairing_method" label="OPNs 配对方式" rules={[{ required: true }]}>
          <Select
            options={[
              { label: "相邻配对", value: "adjacent" },
              { label: "随机配对", value: "random" },
              { label: "相关性贪心配对", value: "correlation_greedy" },
            ]}
          />
        </Form.Item>

        <Form.Item name="test_size" label="测试集比例" rules={[{ required: true }]}>
          <InputNumber min={0.1} max={0.4} step={0.05} />
        </Form.Item>

        <Form.Item name="random_state" label="随机种子" rules={[{ required: true }]}>
          <InputNumber min={0} max={999999} />
        </Form.Item>

        <Button type="primary" htmlType="submit" loading={training}>
          开始训练
        </Button>
      </Form>
    </main>
  );
}
