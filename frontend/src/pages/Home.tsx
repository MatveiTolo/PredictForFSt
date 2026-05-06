import { useState } from "react";
import { Card, Button, Select, Space, Spin, Alert, Row, Col, Typography, Tag } from "antd";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const SYMBOLS = [
  { value: "USDRUB=X", label: "🇺🇸 USD/RUB" },
  { value: "GC=F", label: "🥇 Золото" },
  { value: "BZ=F", label: "🛢️ Нефть Brent" },
];

function Home() {
  const [selectedTicker, setSelectedTicker] = useState("USDRUB=X");
  const [horizon, setHorizon] = useState(7);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchForecast = async () => {
    setLoading(true);
    setError("");
    setData(null);
    try {
      const response = await fetch("http://127.0.0.1:8000/api/forecast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: selectedTicker, horizon }),
      });
      if (!response.ok) throw new Error("Ошибка получения прогноза");
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Подготовка данных для графика
  const chartData = data
    ? [
        ...data.history.dates.map((d: string, i: number) => ({
          date: d,
          цена: data.history.prices[i],
          тип: "История",
        })),
        ...data.forecast.dates.map((d: string, i: number) => ({
          date: d,
          цена: data.forecast.prices[i],
          тип: "Прогноз",
        })),
      ]
    : [];

  return (
    <div>
      <Typography.Title level={2}>Прогноз курса валют</Typography.Title>

      <Card style={{ marginBottom: 20 }}>
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <div>
            <Typography.Text strong>Выберите валюту:</Typography.Text>
            <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
              {SYMBOLS.map((s) => (
                <Col key={s.value}>
                  <Button
                    type={selectedTicker === s.value ? "primary" : "default"}
                    onClick={() => setSelectedTicker(s.value)}
                  >
                    {s.label}
                  </Button>
                </Col>
              ))}
            </Row>
          </div>

          <Space>
            <Typography.Text strong>Горизонт прогноза:</Typography.Text>
            <Select value={horizon} onChange={setHorizon} style={{ width: 100 }}>
              <Select.Option value={3}>3 дня</Select.Option>
              <Select.Option value={7}>7 дней</Select.Option>
              <Select.Option value={14}>14 дней</Select.Option>
              <Select.Option value={30}>30 дней</Select.Option>
            </Select>
          </Space>

          <Button type="primary" size="large" onClick={fetchForecast} disabled={loading}>
            {loading ? <Spin size="small" /> : "Получить прогноз"}
          </Button>
        </Space>
      </Card>

      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 20 }} />}

      {data && (
        <Card title={`Прогноз для ${data.ticker}`}>
          <Row gutter={16} style={{ marginBottom: 20 }}>
            <Col>
              <Card size="small">
                <Typography.Text type="secondary">Текущая цена</Typography.Text>
                <Typography.Title level={3} style={{ margin: 0 }}>
                  {data.history?.prices?.slice(-1)[0]?.toFixed(2)} ₽
                </Typography.Title>
              </Card>
            </Col>
            <Col>
              <Card size="small">
                <Typography.Text type="secondary">Прогноз через {horizon} дн.</Typography.Text>
                <Typography.Title level={3} style={{ margin: 0 }}>
                  {data.forecast?.prices?.slice(-1)[0]?.toFixed(2)} ₽
                  <Tag
                    color={
                      data.forecast.prices.slice(-1)[0] > data.history.prices.slice(-1)[0]
                        ? "green"
                        : "red"
                    }
                    style={{ marginLeft: 8 }}
                  >
                    {data.forecast.prices.slice(-1)[0] > data.history.prices.slice(-1)[0]
                      ? "↑ Рост"
                      : "↓ Падение"}
                  </Tag>
                </Typography.Title>
              </Card>
            </Col>
          </Row>

          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="цена" stroke="#1890ff" dot={false} name="Цена" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  );
}

export default Home;