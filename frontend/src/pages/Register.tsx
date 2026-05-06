import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, Typography, Alert } from "antd";
import { UserOutlined, LockOutlined, MailOutlined } from "@ant-design/icons";

function Register() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { email: string; username: string; password: string }) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("http://127.0.0.1:8000/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : "Ошибка регистрации");
      }
      navigate("/login");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Регистрация" style={{ maxWidth: 400, margin: "40px auto" }}>
      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}
      <Form onFinish={onFinish} layout="vertical">
        <Form.Item name="email" rules={[{ required: true, type: "email", message: "Введите корректный email" }]}>
          <Input prefix={<MailOutlined />} placeholder="Email" size="large" />
        </Form.Item>
        <Form.Item name="username" rules={[{ required: true, min: 3, message: "Минимум 3 символа" }]}>
          <Input prefix={<UserOutlined />} placeholder="Логин" size="large" />
        </Form.Item>
        <Form.Item name="password" rules={[{ required: true, min: 4, message: "Минимум 4 символа" }]}>
          <Input.Password prefix={<LockOutlined />} placeholder="Пароль" size="large" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block size="large">
            Зарегистрироваться
          </Button>
        </Form.Item>
      </Form>
      <Typography.Text>
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </Typography.Text>
    </Card>
  );
}

export default Register;