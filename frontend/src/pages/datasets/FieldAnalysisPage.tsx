import { ArrowLeftOutlined, CheckOutlined, CloseOutlined, QuestionCircleOutlined, ReloadOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Space,
  Spin,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  confirmFieldRecommendations,
  generateFieldAnalysis,
  getFieldRecommendations,
} from "../../api/ai";
import { getDataset } from "../../api/datasets";
import type { Dataset } from "../../types/dataset";
import type { FieldRecommendation } from "../../types/ai";


const RECOMMENDATION_LABELS: Record<string, string> = {
  keep: "保留为特征",
  ignore: "忽略",
  remove: "移除",
  de_identify: "脱敏后保留",
  impute_and_keep: "填补后保留",
  standardize_and_keep: "标准化后保留",
  encode_and_keep: "编码后保留",
  check_for_leakage: "检查泄漏风险",
  manual_review: "人工审核",
};

const RECOMMENDATION_COLORS: Record<string, string> = {
  keep: "blue",
  ignore: "default",
  remove: "red",
  de_identify: "orange",
  impute_and_keep: "cyan",
  standardize_and_keep: "geekblue",
  encode_and_keep: "purple",
  check_for_leakage: "volcano",
  manual_review: "gold",
};

const RISK_COLORS: Record<string, string> = {
  high: "red",
  medium: "orange",
  low: "green",
};

export default function FieldAnalysisPage() {
  const { id } = useParams();
  const datasetId = Number(id);
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [recommendations, setRecommendations] = useState<FieldRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [savingField, setSavingField] = useState<string | null>(null);
  const [decisions, setDecisions] = useState<Record<string, boolean>>({});
  const analysisTriggered = useRef(false);

  const loadExistingAnalysis = useCallback(async () => {
    try {
      const recs = await getFieldRecommendations(datasetId);
      setRecommendations(recs);
      setDecisions(
        Object.fromEntries(
          recs
            .filter((r) => r.user_confirmed != null)
            .map((r) => [r.field, !!r.user_confirmed]),
        ),
      );
      return true;
    } catch {
      return false;
    }
  }, [datasetId]);

  useEffect(() => {
    if (!Number.isFinite(datasetId)) return;
    (async () => {
      setLoading(true);
      try {
        const ds = await getDataset(datasetId);
        setDataset(ds);
        if (!ds.file_path) {
          setLoading(false);
          return;
        }
        // Check for existing analysis first
        const exists = await loadExistingAnalysis();
        if (!exists && !analysisTriggered.current) {
          // Auto-trigger analysis
          analysisTriggered.current = true;
          setAnalyzing(true);
          setLoading(false);
          try {
            await generateFieldAnalysis(datasetId);
            await loadExistingAnalysis();
            message.success("AI 字段分析已完成");
          } catch {
            message.error("AI 字段分析生成失败，请手动重试");
          } finally {
            setAnalyzing(false);
          }
        } else {
          setLoading(false);
        }
      } catch {
        message.error("数据集加载失败");
        setLoading(false);
      }
    })();
  }, [datasetId, loadExistingAnalysis]);

  const handleDecision = useCallback(async (field: string, accepted: boolean) => {
    setSavingField(field);
    try {
      await confirmFieldRecommendations(datasetId, [{ field, accepted, modification: null }]);
      setDecisions((prev) => ({ ...prev, [field]: accepted }));
      await loadExistingAnalysis();
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      message.error(typeof detail === "string" ? detail : "保存失败");
    } finally {
      setSavingField(null);
    }
  }, [datasetId, loadExistingAnalysis]);

  async function handleReanalyze() {
    setAnalyzing(true);
    setRecommendations([]);
    setDecisions({});
    try {
      await generateFieldAnalysis(datasetId);
      await loadExistingAnalysis();
      message.success("AI 字段分析已完成");
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      message.error(typeof detail === "string" ? detail : "分析失败");
    } finally {
      setAnalyzing(false);
    }
  }

  const columns: ColumnsType<FieldRecommendation> = useMemo(
    () => [
      {
        title: "字段名",
        dataIndex: "field",
        width: 160,
        fixed: "left" as const,
        render: (v: string) => <Typography.Text strong>{v}</Typography.Text>,
      },
      {
        title: "AI 建议",
        dataIndex: "recommendation",
        width: 140,
        render: (v: string) => (
          <Tag color={RECOMMENDATION_COLORS[v] ?? "default"}>
            {RECOMMENDATION_LABELS[v] ?? v}
          </Tag>
        ),
      },
      {
        title: "风险等级",
        dataIndex: "risk_level",
        width: 90,
        align: "center" as const,
        render: (v: string) => <Tag color={RISK_COLORS[v] ?? "default"}>{v}</Tag>,
      },
      {
        title: "建议原因",
        dataIndex: "reason",
        ellipsis: true,
        render: (v: string) => (
          <Typography.Text style={{ fontSize: 13 }}>{v}</Typography.Text>
        ),
      },
      {
        title: (
          <Space>
            确认
            <Tooltip title="AI 建议仅作参考，最终由您决定">
              <QuestionCircleOutlined style={{ color: "#1677ff" }} />
            </Tooltip>
          </Space>
        ),
        width: 150,
        render: (_, record) => {
          const decided = record.field in decisions;
          const accepted = decisions[record.field];
          const busy = savingField === record.field;
          return (
            <Space>
              <Button
                size="small"
                type={decided && accepted ? "primary" : "default"}
                icon={<CheckOutlined />}
                loading={busy}
                onClick={() => handleDecision(record.field, true)}
              >
                接受
              </Button>
              <Button
                size="small"
                type={decided && !accepted ? "primary" : "default"}
                danger={decided && !accepted}
                icon={<CloseOutlined />}
                loading={busy}
                onClick={() => handleDecision(record.field, false)}
              >
                拒绝
              </Button>
            </Space>
          );
        },
      },
      {
        title: "需要确认",
        dataIndex: "requires_user_confirmation",
        width: 90,
        align: "center" as const,
        render: (v: boolean) =>
          v ? <Tag color="volcano">是</Tag> : <Tag color="green">否</Tag>,
      },
      {
        title: "状态",
        dataIndex: "user_confirmed",
        width: 90,
        align: "center" as const,
        render: (v: boolean | null) =>
          v == null ? (
            <Tag>待确认</Tag>
          ) : v ? (
            <Tag color="green">已接受</Tag>
          ) : (
            <Tag color="red">已拒绝</Tag>
          ),
      },
    ],
    [decisions, handleDecision, savingField],
  );

  // Loading state
  if (loading) {
    return (
      <main style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <Spin size="large" />
      </main>
    );
  }

  // Error state
  if (!dataset) {
    return (
      <main>
        <Alert type="error" message="数据集不存在或无权访问" />
      </main>
    );
  }

  // Analyzing state — centered spinner
  if (analyzing) {
    return (
      <main>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Typography.Title level={3} style={{ margin: 0 }}>
            {dataset.name} — 字段分析
          </Typography.Title>
          <Button
            icon={<ArrowLeftOutlined />}
            style={{ borderColor: "#1677ff", color: "#1677ff" }}
            onClick={() => navigate(`/datasets/${datasetId}`)}
          >
            返回
          </Button>
        </div>
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 120,
          gap: 24,
        }}>
          <Spin size="large" />
          <Typography.Text type="secondary" style={{ fontSize: 16 }}>
            AI 分析中，请稍候…
          </Typography.Text>
        </div>
      </main>
    );
  }

  return (
    <main>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          {dataset.name} — 字段分析
        </Typography.Title>
        <Space>
          {dataset.file_path && (
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReanalyze}
              loading={analyzing}
            >
              重新分析
            </Button>
          )}
          <Button
            icon={<ArrowLeftOutlined />}
            style={{ borderColor: "#1677ff", color: "#1677ff" }}
            onClick={() => navigate(`/datasets/${datasetId}`)}
          >
            返回
          </Button>
        </Space>
      </div>

      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        {!dataset.file_path && (
          <Alert
            type="warning"
            showIcon
            message="请先上传数据集文件"
            description="AI 字段分析需要数据集中的字段统计信息。"
          />
        )}

        {recommendations.length > 0 && (
          <Table<FieldRecommendation>
            rowKey="field"
            columns={columns}
            dataSource={recommendations}
            pagination={false}
            scroll={{ x: 1100 }}
            size="small"
            locale={{ emptyText: "暂无 AI 建议" }}
          />
        )}
      </Space>
    </main>
  );
}
