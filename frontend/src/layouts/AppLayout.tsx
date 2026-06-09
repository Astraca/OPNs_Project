import {
  BarChartOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  HomeOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import { Button, Layout, Menu, Space, Typography } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuthStore } from "../store/authStore";
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
  const user = useAuthStore((state) => state.user);
  const clearSession = useAuthStore((state) => state.clearSession);

  function handleLogout() {
    clearSession();
    navigate("/login", { replace: true });
  }

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
          <Space>
            <Typography.Text type="secondary">{user?.username}</Typography.Text>
            <Button icon={<LogoutOutlined />} onClick={handleLogout}>
              退出
            </Button>
          </Space>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
