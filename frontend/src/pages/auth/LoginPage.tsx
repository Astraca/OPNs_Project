import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { Alert, Button, Form, Input, Typography, message } from "antd";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { login } from "../../api/auth";
import { useAuthStore } from "../../store/authStore";
import type { LoginPayload } from "../../types/auth";
import "./AuthPages.css";


type LocationState = {
  from?: { pathname?: string };
};

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((state) => state.setSession);
  const [form] = Form.useForm<LoginPayload>();

  async function handleSubmit(values: LoginPayload) {
    try {
      const result = await login(values);
      setSession(result.access_token, result.user);
      const redirectTo = (location.state as LocationState | null)?.from?.pathname ?? "/dashboard";
      navigate(redirectTo, { replace: true });
    } catch {
      message.error("登录失败，请检查账号和密码");
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="auth-title">
          <Typography.Title level={3}>登录</Typography.Title>
          <Typography.Text type="secondary">进入 OPNs IgAN 科研分析系统</Typography.Text>
        </div>
        <Alert
          message="系统结果仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。"
          type="info"
          showIcon
          className="auth-title"
        />
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="username_or_email"
            label="用户名或邮箱"
            rules={[{ required: true, message: "请输入用户名或邮箱" }]}
          >
            <Input prefix={<UserOutlined />} autoComplete="username" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: "请输入密码" }]}
          >
            <Input.Password prefix={<LockOutlined />} autoComplete="current-password" />
          </Form.Item>
          <div className="auth-actions">
            <Link to="/register">创建账号</Link>
            <Button type="primary" htmlType="submit">
              登录
            </Button>
          </div>
        </Form>
      </section>
    </main>
  );
}
