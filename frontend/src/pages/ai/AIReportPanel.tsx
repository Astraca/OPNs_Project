import { DownOutlined, UpOutlined } from "@ant-design/icons";
import { Button, Typography } from "antd";
import { useEffect, useMemo, useRef, useState } from "react";

import type { AIAnalysisReport } from "../../types/ai";


const COLLAPSED_MAX_HEIGHT = 300;

function renderMarkdown(text: string): string {
  let html = text
    // Bold
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    // Headers
    .replace(/^### (.+)$/gm, "<h4>$1</h4>")
    .replace(/^## (.+)$/gm, "<h3>$1</h3>")
    .replace(/^# (.+)$/gm, "<h2>$1</h2>")
    // Numbered lists
    .replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>")
    // Unordered lists
    .replace(/^[-*]\s+(.+)$/gm, "<li>$1</li>")
    // Wrap consecutive <li> in <ul>
    .replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>")
    // Line breaks
    .replace(/\n\n/g, "<br/><br/>")
    .replace(/\n/g, "<br/>");

  // Clean up nested <br/> inside <ul>
  html = html.replace(/<ul>(.+?)<\/ul>/gs, (_m, inner) =>
    `<ul>${inner.replace(/<br\/?>/g, "")}</ul>`,
  );

  return html;
}

type AIReportPanelProps = {
  report: AIAnalysisReport | null;
};

export default function AIReportPanel({ report }: AIReportPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [overflow, setOverflow] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const html = useMemo(
    () => (report ? renderMarkdown(report.generated_text) : ""),
    [report],
  );

  useEffect(() => {
    setExpanded(false);
    setOverflow(false);
    // Check overflow after render
    const timer = setTimeout(() => {
      if (contentRef.current) {
        setOverflow(contentRef.current.scrollHeight > COLLAPSED_MAX_HEIGHT + 16);
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [report]);

  if (!report) {
    return null;
  }

  return (
    <div
      style={{
        background: "#f6ffed",
        border: "1px solid #b7eb8f",
        borderRadius: 8,
        padding: "16px 20px",
        marginBottom: 16,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <Typography.Title level={5} style={{ margin: 0, color: "#52c41a" }}>
          AI 辅助分析
        </Typography.Title>
      </div>
      <div
        ref={contentRef}
        style={{
          maxHeight: expanded ? "none" : COLLAPSED_MAX_HEIGHT,
          overflow: "hidden",
          transition: "max-height 0.3s ease",
        }}
      >
        <Typography.Paragraph style={{ marginBottom: 0, lineHeight: 1.8 }}>
          <span
            dangerouslySetInnerHTML={{ __html: html }}
            style={{ whiteSpace: "pre-line" }}
          />
        </Typography.Paragraph>
      </div>
      {overflow && (
        <div style={{ textAlign: "center", marginTop: 8 }}>
          <Button
            type="link"
            size="small"
            icon={expanded ? <UpOutlined /> : <DownOutlined />}
            onClick={() => setExpanded((prev) => !prev)}
          >
            {expanded ? "收起分析" : "展开分析"}
          </Button>
        </div>
      )}
    </div>
  );
}
