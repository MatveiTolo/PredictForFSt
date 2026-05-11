import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Table, Select, message, Typography, Card, Spin, Alert } from "antd";

interface User {
  username: string;
  email: string;
  role: string;
}

function Admin() {
  const { token, role } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchUsers = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("http://127.0.0.1:8000/admin/users", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Ошибка загрузки пользователей");
      const data = await response.json();
      setUsers(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const changeRole = async (username: string, newRole: string) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/admin/users/${username}/role?role=${newRole}`,
        {
          method: "PUT",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!response.ok) throw new Error("Ошибка смены роли");
      message.success(`Роль пользователя ${username} изменена на ${newRole}`);
      fetchUsers();
    } catch (err: any) {
      message.error(err.message);
    }
  };

  if (role !== "admin") {
    return <Alert message="Доступ запрещён" description="Эта страница доступна только администраторам" type="error" showIcon />;
  }

  if (loading) return <Spin size="large" style={{ display: "block", margin: "40px auto" }} />;
  if (error) return <Alert message={error} type="error" showIcon />;

  const columns = [
    { title: "Имя пользователя", dataIndex: "username", key: "username" },
    { title: "Email", dataIndex: "email", key: "email" },
    {
      title: "Роль",
      dataIndex: "role",
      key: "role",
      render: (role: string, record: User) => (
        <Select
          value={role}
          onChange={(value) => changeRole(record.username, value)}
          style={{ width: 120 }}
        >
          <Select.Option value="user">user</Select.Option>
          <Select.Option value="admin">admin</Select.Option>
        </Select>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={2}>Управление пользователями</Typography.Title>
      <Card>
        <Table dataSource={users} columns={columns} rowKey="username" pagination={false} />
      </Card>
    </div>
  );
}

export default Admin;