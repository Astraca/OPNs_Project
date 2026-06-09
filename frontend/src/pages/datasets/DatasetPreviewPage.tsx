import { Button, Table, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getDatasetPreview } from "../../api/datasets";
import type { DatasetPreview } from "../../types/dataset";
import "./DatasetPages.css";


export default function DatasetPreviewPage() {
  const { id } = useParams();
  const datasetId = Number(id);
  const navigate = useNavigate();
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadPreview() {
      setLoading(true);
      try {
        setPreview(await getDatasetPreview(datasetId));
      } catch {
        message.error("数据预览加载失败");
      } finally {
        setLoading(false);
      }
    }

    if (Number.isFinite(datasetId)) {
      void loadPreview();
    }
  }, [datasetId]);

  const columns: ColumnsType<Record<string, unknown>> = useMemo(
    () =>
      (preview?.columns ?? []).map((column) => ({
        title: column,
        dataIndex: column,
        ellipsis: true,
        render: (value: unknown) => String(value ?? ""),
      })),
    [preview?.columns],
  );

  const rows = useMemo(
    () => (preview?.rows ?? []).map((row, index) => ({ ...row, __row_id: index })),
    [preview?.rows],
  );

  return (
    <main>
      <div className="dataset-toolbar">
        <div>
          <Typography.Title level={3}>数据预览</Typography.Title>
          <Typography.Text type="secondary">默认展示前 50 行，共 {preview?.total_rows ?? 0} 行。</Typography.Text>
        </div>
        <Button onClick={() => navigate(`/datasets/${datasetId}`)}>返回详情</Button>
      </div>
      <Table
        rowKey="__row_id"
        columns={columns}
        dataSource={rows}
        loading={loading}
        scroll={{ x: true }}
        pagination={{ pageSize: 10 }}
      />
    </main>
  );
}
