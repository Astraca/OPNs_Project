import { LockOutlined, MailOutlined, UserOutlined } from "@ant-design/icons";
import { Button, Form, Input, Typography, message } from "antd";
import { Link, useNavigate } from "react-router-dom";

import { register } from "../../api/auth";
import { useAuthStore } from "../../store/authStore";
import type { RegisterPayload } from "../../types/auth";
import "./AuthPages.css";


export default function RegisterPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((state) => state.setSession);
  const [form] = Form.useForm<RegisterPayload>();

  async function handleSubmit(values: RegisterPayload) {
    try {
      const result = await register(values);
      setSession(result.access_token, result.user);
      navigate("/dashboard", { replace: true });
    } catch {
      message.error("注册失败，请更换用户名或邮箱后重试");
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="auth-title">
          <Typography.Title level={3}>注册</Typography.Title>
          <Typography.Text type="secondary">创建科研分析系统账号</Typography.Text>
        </div>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: "请输入用户名" },
              { min: 3, message: "用户名至少 3 个字符" },
            ]}
          >
            <Input prefix={<UserOutlined />} autoComplete="username" />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: "请输入邮箱" },
              { type: "email", message: "请输入有效邮箱" },
            ]}
          >
            <Input prefix={<MailOutlined />} autoComplete="email" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: "请输入密码" },
              { min: 8, message: "密码至少 8 个字符" },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
          </Form.Item>
          <div className="auth-actions">
            <Link to="/login">已有账号</Link>
            <Button type="primary" htmlType="submit">
              注册
            </Button>
          </div>
        </Form>
      </section>
    </main>
  );
}
