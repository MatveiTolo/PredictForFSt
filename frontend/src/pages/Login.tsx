import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, Typography, Alert } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { useAuth } from "../context/AuthContext";

const API_URL = "http://127.0.0.1:8000";

function Login() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Ошибка входа");
      }
      // Теперь принимаем оба токена
      login(data.access_token, data.refresh_token);
      navigate("/");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Вход в систему" style={{ maxWidth: 400, margin: "40px auto" }}>
      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}
      <Form onFinish={onFinish} layout="vertical">
        <Form.Item name="username" rules={[{ required: true, message: "Введите логин" }]}>
          <Input prefix={<UserOutlined />} placeholder="Логин" size="large" />
        </Form.Item>
        <Form.Item name="password" rules={[{ required: true, message: "Введите пароль" }]}>
          <Input.Password prefix={<LockOutlined />} placeholder="Пароль" size="large" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block size="large">
            Войти
          </Button>
        </Form.Item>
      </Form>
      <Typography.Text>
        Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
      </Typography.Text>
    </Card>
  );
}

export default Login;