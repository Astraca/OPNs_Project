import {
  ArrowLeftOutlined,
  DeleteOutlined,
  InfoCircleOutlined,
  NodeIndexOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Popconfirm,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { generateOpnsPairingAnalysis } from "../../api/ai";
import { request } from "../../api/request";
import { deleteModel, getModel, getModelMetadata, getModelMetrics } from "../../api/models";
import type { AIAnalysisReport } from "../../types/ai";
import type { MLModel, ModelMetric } from "../../types/model";
import AIReportPanel from "../ai/AIReportPanel";
import { displayFieldName, displayPairingMethod } from "../../utils/fieldNames";
import "./ModelPages.css";


type MetricRow = {
  target_name: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
  mae?: number;
  rmse?: number;
  r2?: number;
  mape?: number;
};

export default function ModelDetailPage() {
  const { id } = useParams();
  const modelId = Number(id);
  const navigate = useNavigate();
  const [model, setModel] = useState<MLModel | null>(null);
  const [metrics, setMetrics] = useState<ModelMetric[]>([]);
  const [metadata, setMetadata] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [opnsAnalyzing, setOpnsAnalyzing] = useState(false);
  const [opnsReport, setOpnsReport] = useState<AIAnalysisReport | null>(null);
  const [opnsLoaded, setOpnsLoaded] = useState(false);
  const opnsSectionRef = useRef<HTMLDivElement>(null);
  const CLS_HELP_KEY = "metrics_show_cls_help";
  const REG_HELP_KEY = "metrics_show_reg_help";
  const [showClsHelp, setShowClsHelp] = useState(() => localStorage.getItem(CLS_HELP_KEY) !== "false");
  const [showRegHelp, setShowRegHelp] = useState(() => localStorage.getItem(REG_HELP_KEY) !== "false");

  const scrollToOpns = useCallback((behavior: ScrollBehavior = "smooth") => {
    setTimeout(() => {
      opnsSectionRef.current?.scrollIntoView({ behavior, block: "start" });
    }, 150);
  }, []);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [m, met, meta] = await Promise.all([
          getModel(modelId),
          getModelMetrics(modelId),
          getModelMetadata(modelId).catch(() => null),
        ]);
        setModel(m);
        setMetrics(met);
        setMetadata(meta);

        // Load existing OPNs analysis if available
        if (m?.opns_enabled) {
          try {
            const { data } = await request.get<AIAnalysisReport>(
              `/ai/opns-pairing-analysis/${modelId}`,
            );
            setOpnsReport(data);
          } catch { /* no existing analysis */ }
        }
      } catch {
        message.error("模型详情加载失败");
      } finally {
        setLoading(false);
      }
    }
    if (Number.isFinite(modelId)) void load();
  }, [modelId]);

  // Scroll to OPNs section only after explicit generation (not on page load)
  useEffect(() => {
    if (opnsReport && opnsLoaded) {
      scrollToOpns("smooth");
      setOpnsLoaded(false);
    }
  }, [opnsReport, opnsLoaded, scrollToOpns]);

  async function handleDelete() {
    try {
      await deleteModel(modelId);
      message.success("模型已删除");
      navigate("/models", { replace: true });
    } catch {
      message.error("删除失败");
    }
  }

  const isRegression = model?.task_type === "regression";

  const metricRows: MetricRow[] = (() => {
    if (isRegression) {
      const row: MetricRow = { target_name: model?.target_columns[0] ?? "target" };
      metrics.forEach((m) => {
        row[m.metric_name as keyof MetricRow] = m.metric_value as never;
      });
      return [row];
    }
    const grouped = new Map<string, MetricRow>();
    metrics.forEach((m) => {
      const target = m.target_name ?? "overall";
      const row = grouped.get(target) ?? { target_name: target };
      row[m.metric_name as keyof MetricRow] = m.metric_value as never;
      grouped.set(target, row);
    });
    return Array.from(grouped.values());
  })();

  const classificationColumns: ColumnsType<MetricRow> = [
    { title: "标签", dataIndex: "target_name" },
    { title: "Accuracy", dataIndex: "accuracy", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "Precision", dataIndex: "precision", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "Recall", dataIndex: "recall", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "F1", dataIndex: "f1", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
  ];

  const regressionColumns: ColumnsType<MetricRow> = [
    { title: "目标", dataIndex: "target_name" },
    { title: "MAE", dataIndex: "mae", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "RMSE", dataIndex: "rmse", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "R²", dataIndex: "r2", render: (v: number | undefined) => v?.toFixed(4) ?? "-" },
    { title: "MAPE", dataIndex: "mape", render: (v: number | undefined) => v != null ? `${v.toFixed(2)}%` : "-" },
  ];

  return (
    <main>
      <div className="model-toolbar">
        <Typography.Title level={3}>{model?.model_name ?? "模型详情"}</Typography.Title>
        <Space>
          <Button
            type="primary"
            style={{ background: "#52c41a", borderColor: "#52c41a" }}
            icon={<ThunderboltOutlined />}
            onClick={() =>
              navigate(
                `${isRegression
                  ? "/prediction/regression/single"
                  : "/prediction/igan/single"}?modelId=${modelId}`,
              )
            }
          >
            开始预测
          </Button>
          {model?.opns_enabled && (
            <Button
              icon={<NodeIndexOutlined />}
              style={{ color: "#722ed1", borderColor: "#722ed1" }}
              loading={opnsAnalyzing}
              onClick={async () => {
                setOpnsAnalyzing(true);
                try {
                  const report = await generateOpnsPairingAnalysis(modelId);
                  setOpnsReport(report);
                  setOpnsLoaded(true);
                } catch {
                  message.error("OPNs 配对分析生成失败");
                } finally {
                  setOpnsAnalyzing(false);
                }
              }}
            >
              OPNs 配对分析
            </Button>
          )}
          <Popconfirm title="确定删除此模型？" onConfirm={handleDelete}>
            <Button danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
          <Button
            icon={<ArrowLeftOutlined />}
            style={{ borderColor: "#1677ff", color: "#1677ff" }}
            onClick={() => navigate("/models")}
          >
            返回
          </Button>
        </Space>
      </div>

      {model && (
        <Card className="model-section">
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="模型名称">{model.model_name}</Descriptions.Item>
            <Descriptions.Item label="算法">
              <Tag color="blue">{model.algorithm}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="任务类型">
              <Tag color={isRegression ? "orange" : "green"}>
                {isRegression ? "回归" : "分类"}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="OPNs 启用">
              {model.opns_enabled ? <Tag color="blue">是</Tag> : <Tag>否</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="目标字段">
              {model.target_columns.map(displayFieldName).join(", ")}
            </Descriptions.Item>
            <Descriptions.Item label="配对方式">{displayPairingMethod(model.pairing_method)}</Descriptions.Item>
            <Descriptions.Item label="特征数">{model.feature_columns.length}</Descriptions.Item>
            <Descriptions.Item label="数据集 ID">{model.dataset_id}</Descriptions.Item>
            <Descriptions.Item label="模型目录" span={2}>
              <Typography.Text code>{model.model_file_path ?? "-"}</Typography.Text>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间" span={2}>
              {new Date(model.created_at).toLocaleString("zh-CN")}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      <Card title="模型指标" className="model-section">
        {!isRegression && showClsHelp && (
          <Alert
            type="info" showIcon icon={<InfoCircleOutlined />} closable
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
            style={{ marginBottom: 12 }}
          />
        )}
        {!isRegression && !showClsHelp && (
          <Button type="link" size="small" icon={<InfoCircleOutlined />}
            onClick={() => { setShowClsHelp(true); localStorage.setItem(CLS_HELP_KEY, "true"); }}
            style={{ marginBottom: 8, padding: 0 }}>显示指标说明</Button>
        )}
        {isRegression && showRegHelp && (
          <Alert
            type="info" showIcon icon={<InfoCircleOutlined />} closable
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
            style={{ marginBottom: 12 }}
          />
        )}
        {isRegression && !showRegHelp && (
          <Button type="link" size="small" icon={<InfoCircleOutlined />}
            onClick={() => { setShowRegHelp(true); localStorage.setItem(REG_HELP_KEY, "true"); }}
            style={{ marginBottom: 8, padding: 0 }}>显示指标说明</Button>
        )}
        <Table
          rowKey="target_name"
          columns={isRegression ? regressionColumns : classificationColumns}
          dataSource={metricRows}
          loading={loading}
          pagination={false}
        />
      </Card>

      {opnsReport && (
        <div ref={opnsSectionRef} className="model-section">
          <AIReportPanel report={opnsReport} />
        </div>
      )}

      {model && (
        <Card title="特征列表" className="model-section">
          <Space wrap>
            {model.feature_columns.map((f) => (
              <Tag key={f}>{displayFieldName(f)}</Tag>
            ))}
          </Space>
        </Card>
      )}

      {metadata && (
        <Card title="训练元数据" className="model-section">
          <Descriptions bordered size="small" column={2}>
            {Object.entries(metadata).map(([key, value]) => (
              <Descriptions.Item key={key} label={key}>
                {typeof value === "object"
                  ? JSON.stringify(value)
                  : String(value ?? "-")}
              </Descriptions.Item>
            ))}
          </Descriptions>
        </Card>
      )}

    </main>
  );
}
