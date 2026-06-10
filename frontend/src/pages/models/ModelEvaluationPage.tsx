import { ArrowLeftOutlined, InfoCircleOutlined } from "@ant-design/icons";
import { Alert, Button, Descriptions, Empty, Space, Table, Typography, message } from "antd";
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
import ModelMetricsBarChart from "../../components/Charts/ModelMetricsBarChart";
import PredictedVsActualChart from "../../components/Charts/PredictedVsActualChart";
import RegressionMetricsBarChart from "../../components/Charts/RegressionMetricsBarChart";
import ResidualsChart from "../../components/Charts/ResidualsChart";
import RocCurveChart from "../../components/Charts/RocCurveChart";
import type { AIAnalysisReport } from "../../types/ai";
import type {
  ClassificationMetricItem,
  ConfusionMatrixData,
  MLModel,
  ModelMetric,
  PredictedVsActualData,
  RegressionMetricItem,
  ResidualsData,
  RocCurveData,
} from "../../types/model";
import { displayFieldName, displayPairingMethod } from "../../utils/fieldNames";
import "./ModelPages.css";


type MetricRow = {
  target_name: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
};

type RegMetricRow = {
  target_name: string;
  mae: number;
  rmse: number;
  r2: number;
  mape: string;
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
  const CLS_HELP_KEY = "metrics_show_cls_help";
  const REG_HELP_KEY = "metrics_show_reg_help";
  const [showClsHelp, setShowClsHelp] = useState(() => localStorage.getItem(CLS_HELP_KEY) !== "false");
  const [showRegHelp, setShowRegHelp] = useState(() => localStorage.getItem(REG_HELP_KEY) !== "false");

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

  const classificationMetrics: ClassificationMetricItem[] = useMemo(
    () =>
      metricRows.map((row) => ({
        target_name: row.target_name,
        accuracy: row.accuracy ?? 0,
        precision: row.precision ?? 0,
        recall: row.recall ?? 0,
        f1: row.f1 ?? 0,
      })),
    [metricRows],
  );

  const classificationColumns: ColumnsType<MetricRow> = [
    { title: "标签", dataIndex: "target_name" },
    { title: "Accuracy", dataIndex: "accuracy", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "Precision", dataIndex: "precision", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "Recall", dataIndex: "recall", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "F1", dataIndex: "f1", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
  ];

  const regMetricRow: RegMetricRow | null = useMemo(() => {
    if (!regressionMetric) return null;
    const row: Record<string, unknown> = { target_name: model?.target_columns[0] ?? "target" };
    row.mae = regressionMetric.mae;
    row.rmse = regressionMetric.rmse;
    row.r2 = regressionMetric.r2;
    row.mape = regressionMetric.mape != null ? `${regressionMetric.mape.toFixed(2)}%` : "-";
    return row as unknown as RegMetricRow;
  }, [regressionMetric, model]);

  const regressionColumns: ColumnsType<RegMetricRow> = [
    { title: "目标", dataIndex: "target_name" },
    { title: "MAE", dataIndex: "mae", render: (v: number) => v?.toFixed(4) },
    { title: "RMSE", dataIndex: "rmse", render: (v: number) => v?.toFixed(4) },
    { title: "R²", dataIndex: "r2", render: (v: number) => v?.toFixed(4) },
    { title: "MAPE", dataIndex: "mape", render: (v: string) => v },
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
          <Button
            icon={<ArrowLeftOutlined />}
            style={{ borderColor: "#1677ff", color: "#1677ff" }}
            onClick={() => navigate("/models")}
          >
            返回
          </Button>
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
          <Descriptions.Item label="配对方式">{displayPairingMethod(model.pairing_method)}</Descriptions.Item>
          <Descriptions.Item label="测试集比例">{((model.hyperparameters as Record<string,unknown>)?.test_size as number ?? 0.2) * 100}%</Descriptions.Item>
          <Descriptions.Item label="模型目录" span={2}>{model.model_file_path ?? "-"}</Descriptions.Item>
        </Descriptions>
      )}

      {/* Classification metrics — first section */}
      {!isRegression && (
        <>
          <section className="model-section">
            <Typography.Title level={4}>分类指标</Typography.Title>
            {showClsHelp && (
              <Alert
                type="info"
                showIcon
                icon={<InfoCircleOutlined />}
                closable
                onClose={() => { setShowClsHelp(false); localStorage.setItem(CLS_HELP_KEY, "false"); }}
                message="指标说明"
                description={
                  <div style={{ lineHeight: 1.8 }}>
                    <div><strong>Accuracy（准确率）</strong>：预测正确的样本占比，0~1，越高越好。类别不均衡时可能失真。</div>
                    <div><strong>Precision（精确率）</strong>：预测为正例中真正为正例的比例，0~1，越高误报越少。</div>
                    <div><strong>Recall（召回率）</strong>：真正例中被正确识别的比例，0~1，越高漏报越少。</div>
                    <div><strong>F1-score</strong>：Precision 与 Recall 的调和均值，0~1，综合衡量模型性能。</div>
                  </div>
                }
                style={{ marginBottom: 16 }}
              />
            )}
            {!showClsHelp && (
              <Button
                type="link"
                size="small"
                icon={<InfoCircleOutlined />}
                onClick={() => { setShowClsHelp(true); localStorage.setItem(CLS_HELP_KEY, "true"); }}
                style={{ marginBottom: 8, padding: 0 }}
              >
                显示指标说明
              </Button>
            )}
            <Table rowKey="target_name" columns={classificationColumns} dataSource={metricRows} loading={loading} pagination={false} />
          </section>
          <section className="model-section">
            <Typography.Title level={4}>指标对比</Typography.Title>
            <ModelMetricsBarChart metrics={classificationMetrics} />
          </section>
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

      {/* Regression metrics — first section */}
      {isRegression && regressionMetric && (
        <>
          <section className="model-section">
            <Typography.Title level={4}>回归指标</Typography.Title>
            {showRegHelp && (
              <Alert
                type="info"
                showIcon
                icon={<InfoCircleOutlined />}
                closable
                onClose={() => { setShowRegHelp(false); localStorage.setItem(REG_HELP_KEY, "false"); }}
                message="指标说明"
                description={
                  <div style={{ lineHeight: 1.8 }}>
                    <div><strong>MAE（平均绝对误差）</strong>：预测值与真实值之差的绝对值的均值，≥0，越小越好。与目标同单位，直观反映平均误差大小。</div>
                    <div><strong>RMSE（均方根误差）</strong>：误差平方均值的平方根，≥0，越小越好。对大误差更敏感。</div>
                    <div><strong>R²（决定系数）</strong>：模型解释的变异比例，通常 0~1，越接近 1 拟合越好。负值表示模型不如均值预测。</div>
                    <div><strong>MAPE（平均绝对百分比误差）</strong>：误差占真实值的百分比均值，≥0%，越小越好。不同量纲数据间可比较。</div>
                  </div>
                }
                style={{ marginBottom: 16 }}
              />
            )}
            {!showRegHelp && (
              <Button
                type="link"
                size="small"
                icon={<InfoCircleOutlined />}
                onClick={() => { setShowRegHelp(true); localStorage.setItem(REG_HELP_KEY, "true"); }}
                style={{ marginBottom: 8, padding: 0 }}
              >
                显示指标说明
              </Button>
            )}
            {regMetricRow && (
              <Table rowKey="target_name" columns={regressionColumns} dataSource={[regMetricRow]} loading={loading} pagination={false} />
            )}
          </section>
          <section className="model-section">
            <Typography.Title level={4}>指标对比</Typography.Title>
            <RegressionMetricsBarChart metrics={regressionMetric} />
          </section>
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
