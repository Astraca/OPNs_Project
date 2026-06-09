import { BarChartOutlined, DatabaseOutlined, ExperimentOutlined, HomeOutlined } from "@ant-design/icons";
import { Layout, Menu, Typography } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import "./AppLayout.css";


const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: "/dashboard", icon: <HomeOutlined />, label: "系统首页" },
  { key: "/datasets", icon: <DatabaseOutlined />, label: "数据集" },
  { key: "/models", icon: <ExperimentOutlined />, label: "模型训练" },
  { key: "/reports", icon: <BarChartOutlined />, label: "分析报告" },
];

export default function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Layout className="app-shell">
      <Sider className="app-sider" width={232}>
        <div className="app-brand">
          <Typography.Text strong>OPNs IgAN</Typography.Text>
          <Typography.Text type="secondary">科研分析系统</Typography.Text>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Typography.Title level={4}>基于 OPNs-SVM/SVR 的 IgAN 病理标签预测</Typography.Title>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
