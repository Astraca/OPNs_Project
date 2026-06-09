import { Alert, Col, Row, Statistic, Typography } from "antd";


const disclaimer =
  "本系统预测结果仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。实际医学判断应由具有资质的临床医生结合完整病史、检查结果和病理资料完成。";

export default function DashboardPage() {
  return (
    <main>
      <Typography.Title level={3}>系统首页</Typography.Title>
      <Alert message={disclaimer} type="info" showIcon />
      <Row gutter={[16, 16]} className="dashboard-stats">
        <Col xs={24} md={8}>
          <Statistic title="当前阶段" value="基础框架" />
        </Col>
        <Col xs={24} md={8}>
          <Statistic title="核心任务" value="MEST-C 分类" />
        </Col>
        <Col xs={24} md={8}>
          <Statistic title="AI 模式" value="Mock 优先" />
        </Col>
      </Row>
    </main>
  );
}
