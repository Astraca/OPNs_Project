import { Alert, Typography } from "antd";

import type { AIAnalysisReport } from "../../types/ai";


type AIReportPanelProps = {
  report: AIAnalysisReport | null;
};

export default function AIReportPanel({ report }: AIReportPanelProps) {
  if (!report) {
    return null;
  }

  return (
    <Alert
      type="success"
      showIcon
      message="AI 辅助分析"
      description={
        <Typography.Paragraph style={{ whiteSpace: "pre-line", marginBottom: 0 }}>
          {report.generated_text}
        </Typography.Paragraph>
      }
    />
  );
}
