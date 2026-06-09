import { Button, Card, Form, Input, Typography, message } from "antd";
import { useState } from "react";

import { changePassword } from "../../api/auth";
import { useAuthStore } from "../../store/authStore";
import "./SettingsPage.css";


export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);

  async function handleChangePassword(values: { old_password: string; new_password: string }) {
    setSaving(true);
    try {
      await changePassword(values.old_password, values.new_password);
      message.success("密码已修改");
      form.resetFields();
    } catch {
      message.error("密码修改失败，请确认当前密码正确且新密码不少于 8 位");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main>
      <Typography.Title level={3}>账号设置</Typography.Title>

      <Card title="个人信息" className="settings-card">
        <Typography.Paragraph>
          <strong>用户名：</strong>{user?.username}
        </Typography.Paragraph>
        <Typography.Paragraph>
          <strong>邮箱：</strong>{user?.email}
        </Typography.Paragraph>
        <Typography.Paragraph>
          <strong>角色：</strong>{user?.role === "admin" ? "管理员" : "普通用户"}
        </Typography.Paragraph>
      </Card>

      <Card title="修改密码" className="settings-card">
        <Form form={form} layout="vertical" onFinish={handleChangePassword} style={{ maxWidth: 400 }}>
          <Form.Item
            name="old_password"
            label="当前密码"
            rules={[{ required: true, message: "请输入当前密码" }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: "请输入新密码" },
              { min: 8, message: "密码至少 8 位" },
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认新密码"
            dependencies={["new_password"]}
            rules={[
              { required: true, message: "请确认新密码" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("new_password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("两次输入的密码不一致"));
                },
              }),
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={saving}>
            修改密码
          </Button>
        </Form>
      </Card>
    </main>
  );
}
