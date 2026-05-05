import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

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
      if (!response.ok) {
        throw new Error("Ошибка загрузки прогнозов");
      }
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
      if (!response.ok) {
        throw new Error("Ошибка удаления");
      }
      setPredictions(predictions.filter((p) => p.id !== id));
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) return <p>Загрузка...</p>;
  if (error) return <p style={{ color: "red" }}>{error}</p>;

  return (
    <div>
      <h2>Избранные прогнозы</h2>
      {predictions.length === 0 ? (
        <p>У вас пока нет сохранённых прогнозов</p>
      ) : (
        <ul>
          {predictions.map((p) => (
            <li key={p.id} style={{ margin: "10px 0", padding: "10px", border: "1px solid #ccc", borderRadius: "4px" }}>
              <strong>{p.ticker}</strong> — {p.predicted_price.toFixed(2)} ₽
              <br />
              Дата прогноза: {p.date}
              <br />
              <button onClick={() => deletePrediction(p.id)} style={{ marginTop: "5px", color: "red" }}>
                Удалить
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default Favorites;