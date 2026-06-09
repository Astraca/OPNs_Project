import { BarChartOutlined, InboxOutlined, TableOutlined, WarningOutlined } from "@ant-design/icons";
import { Alert, Button, Descriptions, Select, Space, Table, Tag, Typography, Upload, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { UploadProps } from "antd";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getDataset, getDatasetColumns, updateDatasetColumnRoles, uploadDatasetFile } from "../../api/datasets";
import type { Dataset, DatasetColumn, DatasetColumnRole } from "../../types/dataset";
import { displayFieldName } from "../../utils/fieldNames";
import "./DatasetPages.css";


const { Dragger } = Upload;

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
        message.error("文件上传失败，请确认文件格式为 CSV 或 XLSX");
      }
      return false;
    },
  };

  function updateLocalRole(columnName: string, role: DatasetColumnRole) {
    setColumns((current) =>
      current.map((column) => (column.column_name === columnName ? { ...column, role } : column)),
    );
  }

  async function handleSaveRoles() {
    setSavingRoles(true);
    try {
      const updatedColumns = await updateDatasetColumnRoles(
        datasetId,
        columns.map((column) => ({ column_name: column.column_name, role: column.role })),
      );
      setColumns(updatedColumns);
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

  const columnDefinitions: ColumnsType<DatasetColumn> = [
    {
      title: "字段",
      dataIndex: "column_name",
      render: (value: string) => <span title={value}>{displayFieldName(value)}</span>,
    },
    { title: "类型", dataIndex: "data_type" },
    {
      title: "角色",
      dataIndex: "role",
      render: (value: DatasetColumnRole, record) => (
        <Select
          value={value}
          style={{ width: 120 }}
          options={[
            { label: "特征", value: "feature" },
            { label: "目标", value: "target" },
            { label: "忽略", value: "ignored" },
          ]}
          onChange={(nextRole) => updateLocalRole(record.column_name, nextRole)}
        />
      ),
    },
    { title: "缺失值", dataIndex: "missing_count" },
    { title: "唯一值", dataIndex: "unique_count" },
    { title: "均值", dataIndex: "mean", render: (value: number | null) => value?.toFixed(4) ?? "-" },
    { title: "最小值", dataIndex: "min_value", render: (value: number | null) => value?.toFixed(4) ?? "-" },
    { title: "最大值", dataIndex: "max_value", render: (value: number | null) => value?.toFixed(4) ?? "-" },
  ];

  return (
    <main>
      <div className="dataset-toolbar">
        <Typography.Title level={3}>{dataset?.name ?? "数据集详情"}</Typography.Title>
        <Space>
          <Button icon={<TableOutlined />} disabled={!dataset?.file_path} onClick={() => navigate("preview")}>
            预览数据
          </Button>
          <Button icon={<BarChartOutlined />} disabled={!dataset?.file_path} onClick={() => navigate("profile")}>
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
          <Descriptions.Item label="文件类型">{dataset.file_type ?? "未上传"}</Descriptions.Item>
          <Descriptions.Item label="样本数">{dataset.sample_count}</Descriptions.Item>
          <Descriptions.Item label="字段数">{dataset.feature_count}</Descriptions.Item>
          <Descriptions.Item label="目标字段" span={2}>
            {dataset.target_columns.length
              ? dataset.target_columns.map(displayFieldName).join(", ")
              : "暂未识别"}
          </Descriptions.Item>
          <Descriptions.Item label="说明" span={2}>
            {dataset.description ?? "-"}
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
          <p className="ant-upload-text">上传数据文件（CSV / XLSX / TXT / DAT / DATA）</p>
          <p className="ant-upload-hint">系统会自动检测分隔符和表头，读取字段类型、缺失值、唯一值并尝试识别目标字段。</p>
        </Dragger>
      </section>

      <section className="dataset-section">
        <Typography.Title level={4}>字段统计</Typography.Title>
        <Space className="dataset-role-actions">
          <Tag color="blue">feature 参与训练和输入统计</Tag>
          <Tag color="green">target 作为预测目标</Tag>
          <Tag>ignored 不参与统计、热力图和训练</Tag>
          <Button type="primary" onClick={handleSaveRoles} loading={savingRoles}>
            保存字段角色
          </Button>
        </Space>
        <Table
          rowKey="id"
          columns={columnDefinitions}
          dataSource={columns}
          loading={loading}
          scroll={{ x: true }}
        />
      </section>
    </main>
  );
}
