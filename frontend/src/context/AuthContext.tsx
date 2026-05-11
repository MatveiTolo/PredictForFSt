import { createContext, useContext, useState, useEffect, useCallback } from "react";
import type { ReactNode } from "react";

const API_URL = "http://127.0.0.1:8000";

interface AuthContextType {
  token: string | null;
  refreshToken: string | null;
  username: string | null;
  role: string | null;
  login: (access: string, refresh: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  refreshToken: null,
  username: null,
  role: null,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [refreshToken, setRefreshToken] = useState<string | null>(localStorage.getItem("refresh_token"));
  const [username, setUsername] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);

  // Загрузка профиля при наличии токена
  useEffect(() => {
    if (token) {
      fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(async (res) => {
          if (res.ok) {
            const data = await res.json();
            setUsername(data.username);
            setRole(data.role || "user");
          } else {
            // Токен истёк — пробуем обновить
            tryRefreshToken();
          }
        })
        .catch(() => tryRefreshToken());
    }
  }, [token]);

  // Обновление токена по refresh
  const tryRefreshToken = useCallback(async () => {
    if (!refreshToken) {
      fullLogout();
      return;
    }
    try {
      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        setToken(data.access_token);
        setRefreshToken(data.refresh_token);
      } else {
        fullLogout();
      }
    } catch {
      fullLogout();
    }
  }, [refreshToken]);

  const login = (access: string, refresh: string) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
    setToken(access);
    setRefreshToken(refresh);
  };

  const fullLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken(null);
    setRefreshToken(null);
    setUsername(null);
    setRole(null);
  };

  const logout = async () => {
    if (token && refreshToken) {
      try {
        await fetch(`${API_URL}/auth/logout?refresh_token=${refreshToken}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {}
    }
    fullLogout();
  };

  return (
    <AuthContext.Provider value={{ token, refreshToken, username, role, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}