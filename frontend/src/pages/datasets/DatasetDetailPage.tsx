import {
  BarChartOutlined,
  InboxOutlined,
  TableOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import type { UploadProps } from "antd";
import {
  Alert,
  Button,
  Descriptions,
  Progress,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  Upload,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getDataset,
  getDatasetColumns,
  updateDatasetColumnRoles,
  uploadDatasetFile,
} from "../../api/datasets";
import type { Dataset, DatasetColumn, DatasetColumnRole } from "../../types/dataset";
import { displayFieldName } from "../../utils/fieldNames";
import "./DatasetPages.css";


const { Dragger } = Upload;

const DATA_TYPE_COLORS: Record<string, string> = {
  int64: "cyan",
  float64: "geekblue",
  object: "purple",
  bool: "orange",
  datetime64: "magenta",
};

function formatDataType(dtype: string): string {
  if (dtype.startsWith("int")) return "整数";
  if (dtype.startsWith("float")) return "小数";
  if (dtype === "object") return "文本";
  if (dtype.startsWith("bool")) return "布尔";
  if (dtype.startsWith("datetime")) return "日期";
  return dtype;
}

export default function DatasetDetailPage() {
  const { id } = useParams();
  const datasetId = Number(id);
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [columns, setColumns] = useState<DatasetColumn[]>([]);
  const [loading, setLoading] = useState(false);
  const [savingRoles, setSavingRoles] = useState(false);

  const loadDataset = useCallback(async () => {
    setLoading(true);
    try {
      const nextDataset = await getDataset(datasetId);
      setDataset(nextDataset);
      if (nextDataset.file_path) {
        setColumns(await getDatasetColumns(datasetId));
      }
    } catch {
      message.error("数据集详情加载失败");
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  const uploadProps: UploadProps = {
    name: "file",
    multiple: false,
    accept: ".csv,.xlsx,.txt,.dat,.data",
    showUploadList: false,
    beforeUpload: async (file) => {
      try {
        const updated = await uploadDatasetFile(datasetId, file);
        setDataset(updated);
        setColumns(await getDatasetColumns(datasetId));
        message.success("文件上传成功");
      } catch {
        message.error("文件上传失败，请确认文件格式是否正确");
      }
      return false;
    },
  };

  function updateLocalRole(columnName: string, role: DatasetColumnRole) {
    setColumns((current) =>
      current.map((col) =>
        col.column_name === columnName ? { ...col, role } : col,
      ),
    );
  }

  async function handleSaveRoles() {
    setSavingRoles(true);
    try {
      const updated = await updateDatasetColumnRoles(
        datasetId,
        columns.map((col) => ({
          column_name: col.column_name,
          role: col.role,
        })),
      );
      setColumns(updated);
      setDataset(await getDataset(datasetId));
      message.success("字段角色已保存");
    } catch {
      message.error("字段角色保存失败");
    } finally {
      setSavingRoles(false);
    }
  }

  useEffect(() => {
    if (Number.isFinite(datasetId)) {
      void loadDataset();
    }
  }, [datasetId, loadDataset]);

  const roleCounts = useMemo(() => {
    const totalRows = dataset?.sample_count ?? 1;
    const feature = columns.filter((c) => c.role === "feature").length;
    const target = columns.filter((c) => c.role === "target").length;
    const ignored = columns.filter((c) => c.role === "ignored").length;
    // Usable features: role=feature AND not constant AND not all-missing
    const usable = columns.filter(
      (c) =>
        c.role === "feature" &&
        c.unique_count > 1 &&
        c.missing_count < totalRows,
    ).length;
    const lowQuality = feature - usable;
    return { feature, target, ignored, usable, lowQuality };
  }, [columns, dataset?.sample_count]);

  const columnDefinitions: ColumnsType<DatasetColumn> = useMemo(
    () => [
      {
        title: "#",
        width: 48,
        align: "center" as const,
        render: (_value, _record, index) => (
          <Typography.Text
            type="secondary"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            {index + 1}
          </Typography.Text>
        ),
      },
      {
        title: "字段名",
        dataIndex: "column_name",
        width: 180,
        fixed: "left" as const,
        render: (value: string) => (
          <Tooltip title={value}>
            <Typography.Text strong>
              {displayFieldName(value)}
            </Typography.Text>
          </Tooltip>
        ),
      },
      {
        title: "类型",
        dataIndex: "data_type",
        width: 80,
        align: "center" as const,
        render: (value: string) => {
          const colorKey =
            Object.keys(DATA_TYPE_COLORS).find((k) => value.startsWith(k)) ?? "";
          return (
            <Tag
              color={DATA_TYPE_COLORS[colorKey] ?? "default"}
              style={{ margin: 0 }}
            >
              {formatDataType(value)}
            </Tag>
          );
        },
      },
      {
        title: "角色",
        dataIndex: "role",
        width: 140,
        render: (value: DatasetColumnRole, record: DatasetColumn) => (
          <Select
            value={value}
            size="small"
            style={{ width: 110 }}
            options={[
              { label: "🔵 特征", value: "feature" },
              { label: "🟢 目标", value: "target" },
              { label: "🟠 忽略", value: "ignored" },
            ]}
            onChange={(nextRole) =>
              updateLocalRole(record.column_name, nextRole)
            }
          />
        ),
      },
      {
        title: "缺失",
        dataIndex: "missing_count",
        width: 130,
        sorter: (a: DatasetColumn, b: DatasetColumn) =>
          a.missing_count - b.missing_count,
        render: (value: number) => {
          const total = dataset?.sample_count || 1;
          const rate = total > 0 ? value / total : 0;
          const hasMissing = value > 0;

          let color = "#9ca3af";
          if (hasMissing) {
            if (rate > 0.3) color = "#dc2626";
            else if (rate > 0.1) color = "#d97706";
            else color = "#16a34a";
          }

          return (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <Typography.Text
                style={{
                  color,
                  fontWeight: hasMissing ? 600 : 400,
                  fontVariantNumeric: "tabular-nums",
                  minWidth: 28,
                }}
              >
                {value}
              </Typography.Text>
              {hasMissing && (
                <Tooltip title={`缺失率 ${(rate * 100).toFixed(1)}%`}>
                  <Progress
                    percent={Math.min(rate * 100, 100)}
                    size="small"
                    showInfo={false}
                    strokeColor={color}
                    trailColor="#f3f4f6"
                    style={{ flex: 1, minWidth: 40, margin: 0 }}
                  />
                </Tooltip>
              )}
            </div>
          );
        },
      },
      {
        title: "唯一值",
        dataIndex: "unique_count",
        width: 80,
        align: "center" as const,
        sorter: (a: DatasetColumn, b: DatasetColumn) =>
          a.unique_count - b.unique_count,
        render: (value: number) => (
          <Typography.Text style={{ fontVariantNumeric: "tabular-nums" }}>
            {value}
          </Typography.Text>
        ),
      },
      {
        title: "均值",
        dataIndex: "mean",
        width: 110,
        align: "right" as const,
        sorter: (a: DatasetColumn, b: DatasetColumn) =>
          (a.mean ?? 0) - (b.mean ?? 0),
        render: (value: number | null) =>
          value != null ? (
            <Typography.Text style={{ fontVariantNumeric: "tabular-nums" }}>
              {value.toFixed(4)}
            </Typography.Text>
          ) : (
            <Typography.Text type="secondary">-</Typography.Text>
          ),
      },
      {
        title: "标准差",
        dataIndex: "std",
        width: 110,
        align: "right" as const,
        render: (value: number | null) =>
          value != null ? (
            <Typography.Text style={{ fontVariantNumeric: "tabular-nums" }}>
              {value.toFixed(4)}
            </Typography.Text>
          ) : (
            <Typography.Text type="secondary">-</Typography.Text>
          ),
      },
      {
        title: "最小值",
        dataIndex: "min_value",
        width: 110,
        align: "right" as const,
        render: (value: number | null) =>
          value != null ? (
            <Typography.Text style={{ fontVariantNumeric: "tabular-nums" }}>
              {value.toFixed(4)}
            </Typography.Text>
          ) : (
            <Typography.Text type="secondary">-</Typography.Text>
          ),
      },
      {
        title: "最大值",
        dataIndex: "max_value",
        width: 110,
        align: "right" as const,
        render: (value: number | null) =>
          value != null ? (
            <Typography.Text style={{ fontVariantNumeric: "tabular-nums" }}>
              {value.toFixed(4)}
            </Typography.Text>
          ) : (
            <Typography.Text type="secondary">-</Typography.Text>
          ),
      },
    ],
    [dataset?.sample_count],
  );

  return (
    <main>
      <div className="dataset-toolbar">
        <Typography.Title level={3}>
          {dataset?.name ?? "数据集详情"}
        </Typography.Title>
        <Space>
          <Button
            icon={<TableOutlined />}
            disabled={!dataset?.file_path}
            onClick={() => navigate("preview")}
          >
            预览数据
          </Button>
          <Button
            icon={<BarChartOutlined />}
            disabled={!dataset?.file_path}
            onClick={() => navigate("profile")}
          >
            数据分析
          </Button>
        </Space>
      </div>

      {dataset && (
        <Descriptions bordered column={2} size="small">
          <Descriptions.Item label="任务类型">
            {dataset.task_type === "multi_output_classification"
              ? "多标签分类"
              : dataset.task_type === "classification"
                ? "单标签分类"
                : "回归"}
          </Descriptions.Item>
          <Descriptions.Item label="文件类型">
            {dataset.file_type ?? "未上传"}
          </Descriptions.Item>
          <Descriptions.Item label="样本数">
            {dataset.sample_count}
          </Descriptions.Item>
          <Descriptions.Item label="字段数">
            {dataset.feature_count}
          </Descriptions.Item>
          <Descriptions.Item label="目标字段" span={2}>
            {dataset.target_columns.length
              ? dataset.target_columns.map(displayFieldName).join(", ")
              : "暂未识别"}
          </Descriptions.Item>
          <Descriptions.Item label="说明" span={2}>
            <Typography.Paragraph style={{ whiteSpace: "pre-line", margin: 0 }}>
              {dataset.description ?? "-"}
            </Typography.Paragraph>
          </Descriptions.Item>
        </Descriptions>
      )}

      {dataset?.file_path && !dataset.target_columns.length && (
        <Alert
          type="warning"
          showIcon
          icon={<WarningOutlined />}
          message="未识别到目标字段"
          description="系统未能自动识别目标列（非 IgAN 数据通常没有 'out-' 前缀列）。请在下方字段统计表中将目标列的角色改为 'target'，然后点击「保存字段角色」。"
          className="dataset-section"
        />
      )}

      <section className="dataset-section dataset-upload">
        <Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">
            上传数据文件（CSV / XLSX / TXT / DAT / DATA）
          </p>
          <p className="ant-upload-hint">
            系统会自动检测分隔符和表头，读取字段类型、缺失值、唯一值并尝试识别目标字段。
          </p>
        </Dragger>
      </section>

      {columns.length > 0 && (
        <section className="dataset-section">
          <div className="dataset-columns-header">
            <div className="dataset-columns-title">
              <Typography.Title level={4} style={{ margin: 0 }}>
                字段统计
              </Typography.Title>
              <Typography.Text type="secondary">
                共 {columns.length} 个字段{" · "}
                可用特征 {roleCounts.usable}{" · "}
                目标 {roleCounts.target}{" · "}
                忽略 {roleCounts.ignored}
                {roleCounts.lowQuality > 0 && (
                  <Typography.Text type="warning">
                    {" · "}低质量 {roleCounts.lowQuality}（常量/全缺失，已自动忽略）
                  </Typography.Text>
                )}
              </Typography.Text>
            </div>
            <Space wrap>
              <Tag color="blue">特征</Tag>
              <Tag color="green">目标</Tag>
              <Tag color="orange">忽略</Tag>
              <Button
                type="primary"
                onClick={handleSaveRoles}
                loading={savingRoles}
              >
                保存字段角色
              </Button>
            </Space>
          </div>
          <div className="dataset-columns-table">
            <Table<DatasetColumn>
              rowKey="id"
              columns={columnDefinitions}
              dataSource={columns}
              loading={loading}
              pagination={false}
              scroll={{ x: 1130, y: 520 }}
              size="small"
              rowClassName={(_record, index) =>
                index % 2 === 0 ? "table-row-even" : "table-row-odd"
              }
              showSorterTooltip={{ title: "点击排序" }}
              locale={{ emptyText: "暂无字段数据" }}
            />
          </div>
        </section>
      )}
    </main>
  );
}
