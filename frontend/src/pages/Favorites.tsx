import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, List, Button, Typography, Alert, Spin, Tag, Popconfirm } from "antd";
import { DeleteOutlined } from "@ant-design/icons";

interface Prediction {
  id: number;
  ticker: string;
  date: string;
  predicted_price: number;
  created_at: string;
}

function Favorites() {
  const { token } = useAuth();
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchPredictions = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("http://127.0.0.1:8000/predictions", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Ошибка загрузки");
      const data = await response.json();
      setPredictions(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, []);

  const deletePrediction = async (id: number) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/predictions/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Ошибка удаления");
      setPredictions(predictions.filter((p) => p.id !== id));
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) return <Spin size="large" style={{ display: "block", margin: "40px auto" }} />;
  if (error) return <Alert message={error} type="error" showIcon />;

  return (
    <div>
      <Typography.Title level={2}>Избранные прогнозы</Typography.Title>
      {predictions.length === 0 ? (
        <Alert message="У вас пока нет сохранённых прогнозов" type="info" showIcon />
      ) : (
        <List
          grid={{ gutter: 16, column: 1 }}
          dataSource={predictions}
          renderItem={(p) => (
            <List.Item>
              <Card
                actions={[
                  <Popconfirm
                    title="Удалить прогноз?"
                    onConfirm={() => deletePrediction(p.id)}
                    okText="Да"
                    cancelText="Нет"
                  >
                    <Button type="link" danger icon={<DeleteOutlined />}>
                      Удалить
                    </Button>
                  </Popconfirm>,
                ]}
              >
                <Card.Meta
                  title={
                    <span>
                      {p.ticker}{" "}
                      <Tag color="blue">{p.predicted_price.toFixed(2)} ₽</Tag>
                    </span>
                  }
                  description={`Дата прогноза: ${p.date} | Создан: ${new Date(p.created_at).toLocaleString()}`}
                />
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  );
}

export default Favorites;