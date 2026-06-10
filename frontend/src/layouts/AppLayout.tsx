import {
  BarChartOutlined,
  BulbOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  HomeOutlined,
  LogoutOutlined,
  SettingOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import type { MenuProps } from "antd";
import { Button, Layout, Menu, Space, Typography } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuthStore } from "../store/authStore";
import "./AppLayout.css";


const { Header, Sider, Content } = Layout;

type NavItem = {
  key: string;
  icon?: React.ReactNode;
  label: string;
  children?: NavItem[];
};

const navItems: NavItem[] = [
  { key: "/dashboard", icon: <HomeOutlined />, label: "系统首页" },
  { key: "/datasets", icon: <DatabaseOutlined />, label: "数据集" },
  { key: "/models", icon: <ExperimentOutlined />, label: "模型训练" },
  {
    key: "prediction-group",
    icon: <ThunderboltOutlined />,
    label: "预测",
    children: [
      { key: "/prediction/igan/single", label: "分类单样本" },
      { key: "/prediction/batch", label: "分类批量" },
      { key: "/prediction/regression/single", label: "回归单样本" },
      { key: "/prediction/regression/batch", label: "回归批量" },
      { key: "/prediction/history", label: "预测历史" },
    ],
  },
  {
    key: "ai-group",
    icon: <BulbOutlined />,
    label: "AI 分析",
    children: [
      { key: "/ai/analysis", label: "AI 辅助分析" },
    ],
  },
  {
    key: "reports-group",
    icon: <BarChartOutlined />,
    label: "实验报告",
    children: [
      { key: "/reports", label: "报告列表" },
      { key: "/reports/generate", label: "生成报告" },
    ],
  },
  {
    key: "settings-group",
    icon: <SettingOutlined />,
    label: "系统设置",
    children: [
      { key: "/settings", label: "账号设置" },
      { key: "/settings/ai", label: "AI 配置" },
    ],
  },
];

function collectLeafKeys(items: NavItem[]): string[] {
  return items.flatMap((item) =>
    item.children ? item.children.map((child) => child.key) : [item.key],
  );
}

function collectOpenKeys(items: NavItem[], pathname: string): string[] {
  return items
    .filter((item) => item.children?.some((child) => pathname.startsWith(child.key)))
    .map((item) => item.key);
}

export default function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const clearSession = useAuthStore((state) => state.clearSession);

  const leafKeys = collectLeafKeys(navItems);
  const selectedKey = leafKeys
    .filter((key) => location.pathname === key || location.pathname.startsWith(`${key}/`))
    .sort((a, b) => b.length - a.length)[0] ?? "/dashboard";
  const openKeys = collectOpenKeys(navItems, location.pathname);

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
          selectedKeys={selectedKey ? [selectedKey] : []}
          defaultOpenKeys={openKeys}
          items={navItems as MenuProps["items"]}
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
