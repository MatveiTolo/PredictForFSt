import { BrowserRouter, Routes, Route, Link, useNavigate } from "react-router-dom";
import { Layout, Menu, Button, Typography, Space } from "antd";
import { HomeOutlined, LoginOutlined, UserAddOutlined, StarOutlined, LogoutOutlined, UserOutlined } from "@ant-design/icons";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Favorites from "./pages/Favorites";
import { AuthProvider, useAuth } from "./context/AuthContext";

const { Header, Content } = Layout;

function NavBar() {
  const { token, username, logout } = useAuth();
  const navigate = useNavigate();

  const menuItems = token
    ? [
        { key: "/", icon: <HomeOutlined />, label: <Link to="/">Главная</Link> },
        { key: "/favorites", icon: <StarOutlined />, label: <Link to="/favorites">Избранное</Link> },
      ]
    : [
        { key: "/", icon: <HomeOutlined />, label: <Link to="/">Главная</Link> },
        { key: "/login", icon: <LoginOutlined />, label: <Link to="/login">Войти</Link> },
        { key: "/register", icon: <UserAddOutlined />, label: <Link to="/register">Регистрация</Link> },
      ];

  return (
    <Header style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
      <Typography.Title level={3} style={{ color: "white", margin: 0 }}>
        🏦 PredictForFSt
      </Typography.Title>
      <Space>
        <Menu
          theme="dark"
          mode="horizontal"
          items={menuItems}
          style={{ flex: 1, minWidth: 300 }}
        />
        {token && (
          <Space style={{ color: "white" }}>
            <UserOutlined />
            <span>{username}</span>
            <Button type="link" icon={<LogoutOutlined />} onClick={logout} style={{ color: "white" }}>
              Выйти
            </Button>
          </Space>
        )}
      </Space>
    </Header>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout style={{ minHeight: "100vh" }}>
          <NavBar />
          <Content style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto", width: "100%" }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/favorites" element={<Favorites />} />
            </Routes>
          </Content>
        </Layout>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;