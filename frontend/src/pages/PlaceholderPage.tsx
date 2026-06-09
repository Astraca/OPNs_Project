import { Typography } from "antd";


type PlaceholderPageProps = {
  title: string;
};

export default function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <main>
      <Typography.Title level={3}>{title}</Typography.Title>
      <Typography.Paragraph type="secondary">该模块将在后续阶段实现。</Typography.Paragraph>
    </main>
  );
}
