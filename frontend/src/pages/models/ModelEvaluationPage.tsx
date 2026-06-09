import { Button, Descriptions, Empty, Space, Table, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { generateModelAnalysis } from "../../api/ai";
import {
  getConfusionMatrices,
  getModel,
  getModelMetrics,
  getPredictedVsActual,
  getRegressionMetrics,
  getResiduals,
  getRocCurves,
} from "../../api/models";
import AIReportPanel from "../ai/AIReportPanel";
import ConfusionMatrixHeatmap from "../../components/Charts/ConfusionMatrixHeatmap";
import PredictedVsActualChart from "../../components/Charts/PredictedVsActualChart";
import ResidualsChart from "../../components/Charts/ResidualsChart";
import RocCurveChart from "../../components/Charts/RocCurveChart";
import type { AIAnalysisReport } from "../../types/ai";
import type {
  ConfusionMatrixData,
  MLModel,
  ModelMetric,
  PredictedVsActualData,
  RegressionMetricItem,
  ResidualsData,
  RocCurveData,
} from "../../types/model";
import { displayFieldName } from "../../utils/fieldNames";
import "./ModelPages.css";


type MetricRow = {
  target_name: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
};

export default function ModelEvaluationPage() {
  const { id } = useParams();
  const modelId = Number(id);
  const navigate = useNavigate();
  const [model, setModel] = useState<MLModel | null>(null);
  const [metrics, setMetrics] = useState<ModelMetric[]>([]);
  const [aiReport, setAiReport] = useState<AIAnalysisReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [generatingAI, setGeneratingAI] = useState(false);

  // Classification charts
  const [confusionMatrices, setConfusionMatrices] = useState<ConfusionMatrixData[]>([]);
  const [rocCurves, setRocCurves] = useState<RocCurveData[]>([]);

  // Regression charts
  const [regressionMetric, setRegressionMetric] = useState<RegressionMetricItem | null>(null);
  const [predictedVsActual, setPredictedVsActual] = useState<PredictedVsActualData | null>(null);
  const [residuals, setResiduals] = useState<ResidualsData | null>(null);

  const isRegression = model?.task_type === "regression";

  useEffect(() => {
    async function loadModel() {
      setLoading(true);
      try {
        const nextModel = await getModel(modelId);
        setModel(nextModel);
        const nextMetrics = await getModelMetrics(modelId);
        setMetrics(nextMetrics);

        if (nextModel.task_type === "regression") {
          const [regMetrics, pva, res] = await Promise.all([
            getRegressionMetrics(modelId).catch(() => null),
            getPredictedVsActual(modelId).catch(() => null),
            getResiduals(modelId).catch(() => null),
          ]);
          if (regMetrics) setRegressionMetric(regMetrics.metrics);
          if (pva) setPredictedVsActual(pva);
          if (res) setResiduals(res);
        } else {
          const [cm, roc] = await Promise.all([
            getConfusionMatrices(modelId).catch(() => [] as ConfusionMatrixData[]),
            getRocCurves(modelId).catch(() => [] as RocCurveData[]),
          ]);
          setConfusionMatrices(cm);
          setRocCurves(roc);
        }
      } catch {
        message.error("模型评估加载失败");
      } finally {
        setLoading(false);
      }
    }

    if (Number.isFinite(modelId)) {
      void loadModel();
    }
  }, [modelId]);

  const metricRows = useMemo(() => {
    const grouped = new Map<string, MetricRow>();
    metrics.forEach((m) => {
      const target = m.target_name ?? "overall";
      const row = grouped.get(target) ?? { target_name: target };
      row[m.metric_name as keyof MetricRow] = m.metric_value as never;
      grouped.set(target, row);
    });
    return Array.from(grouped.values());
  }, [metrics]);

  const classificationColumns: ColumnsType<MetricRow> = [
    { title: "标签", dataIndex: "target_name" },
    { title: "Accuracy", dataIndex: "accuracy", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "Precision", dataIndex: "precision", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "Recall", dataIndex: "recall", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "F1", dataIndex: "f1", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
  ];

  async function handleGenerateAI() {
    setGeneratingAI(true);
    try {
      setAiReport(await generateModelAnalysis(modelId));
      message.success("AI 模型分析已生成");
    } catch {
      message.error("AI 模型分析生成失败");
    } finally {
      setGeneratingAI(false);
    }
  }

  return (
    <main>
      <div className="model-toolbar">
        <Typography.Title level={3}>模型评估</Typography.Title>
        <Space>
          <Button onClick={handleGenerateAI} loading={generatingAI}>生成 AI 结果分析</Button>
          <Button onClick={() => navigate("/models")}>返回模型列表</Button>
        </Space>
      </div>
      <AIReportPanel report={aiReport} />

      {model && (
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="模型名称">{model.model_name}</Descriptions.Item>
          <Descriptions.Item label="算法">{model.algorithm}</Descriptions.Item>
          <Descriptions.Item label="任务类型">{isRegression ? "回归" : "分类"}</Descriptions.Item>
          <Descriptions.Item label="目标字段">{model.target_columns.map(displayFieldName).join(", ")}</Descriptions.Item>
          <Descriptions.Item label="特征数">{model.feature_columns.length}</Descriptions.Item>
          <Descriptions.Item label="配对方式">{model.pairing_method ?? "-"}</Descriptions.Item>
          <Descriptions.Item label="模型目录" span={2}>{model.model_file_path ?? "-"}</Descriptions.Item>
        </Descriptions>
      )}

      {/* Classification metrics */}
      {!isRegression && (
        <section className="model-section">
          <Typography.Title level={4}>分类指标</Typography.Title>
          <Table rowKey="target_name" columns={classificationColumns} dataSource={metricRows} loading={loading} />
        </section>
      )}

      {/* Regression metrics */}
      {isRegression && regressionMetric && (
        <section className="model-section">
          <Typography.Title level={4}>回归指标</Typography.Title>
          <Descriptions bordered size="small" column={4}>
            <Descriptions.Item label="MAE">{regressionMetric.mae.toFixed(4)}</Descriptions.Item>
            <Descriptions.Item label="RMSE">{regressionMetric.rmse.toFixed(4)}</Descriptions.Item>
            <Descriptions.Item label="R²">{regressionMetric.r2.toFixed(4)}</Descriptions.Item>
            <Descriptions.Item label="MAPE">
              {regressionMetric.mape != null ? `${regressionMetric.mape.toFixed(2)}%` : "-"}
            </Descriptions.Item>
          </Descriptions>
        </section>
      )}

      {/* Classification charts */}
      {!isRegression && (
        <>
          <section className="model-section">
            <Typography.Title level={4}>混淆矩阵</Typography.Title>
            {confusionMatrices.length > 0 ? (
              <ConfusionMatrixHeatmap data={confusionMatrices} />
            ) : (
              <Empty description={loading ? "加载中..." : "暂无数据"} />
            )}
          </section>
          <section className="model-section">
            <Typography.Title level={4}>ROC 曲线</Typography.Title>
            {rocCurves.length > 0 ? (
              <RocCurveChart data={rocCurves} />
            ) : (
              <Empty description={loading ? "加载中..." : "暂无数据"} />
            )}
          </section>
        </>
      )}

      {/* Regression charts */}
      {isRegression && (
        <>
          <section className="model-section">
            <Typography.Title level={4}>真实值-预测值散点图</Typography.Title>
            {predictedVsActual ? (
              <PredictedVsActualChart data={predictedVsActual} />
            ) : (
              <Empty description={loading ? "加载中..." : "暂无数据"} />
            )}
          </section>
          <section className="model-section">
            <Typography.Title level={4}>残差分布图</Typography.Title>
            {residuals ? (
              <ResidualsChart data={residuals} />
            ) : (
              <Empty description={loading ? "加载中..." : "暂无数据"} />
            )}
          </section>
        </>
      )}
    </main>
  );
}
