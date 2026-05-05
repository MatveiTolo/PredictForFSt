import { useState } from "react";

const SYMBOLS = [
  { value: "USDRUB=X", label: "USD/RUB 🇺🇸" },
  { value: "GC=F", label: "Золото 🥇" },
  { value: "BZ=F", label: "Нефть Brent 🛢️" },
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
      if (!response.ok) {
        throw new Error("Ошибка получения прогноза");
      }
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Текущие курсы и прогноз</h2>

      <div style={{ margin: "10px 0" }}>
        {SYMBOLS.map((s) => (
          <button
            key={s.value}
            onClick={() => setSelectedTicker(s.value)}
            style={{
              margin: "0 5px",
              padding: "8px 16px",
              background: selectedTicker === s.value ? "#4CAF50" : "#ddd",
              color: selectedTicker === s.value ? "white" : "black",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div style={{ margin: "10px 0" }}>
        <label>Горизонт прогноза (дней): </label>
        <select value={horizon} onChange={(e) => setHorizon(Number(e.target.value))}>
          <option value="3">3</option>
          <option value="7">7</option>
          <option value="14">14</option>
          <option value="30">30</option>
        </select>
      </div>

      <button onClick={fetchForecast} disabled={loading} style={{ padding: "10px 20px", cursor: "pointer" }}>
        {loading ? "Загрузка..." : "Получить прогноз"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {data && (
        <div style={{ marginTop: "20px" }}>
          <h3>Прогноз для {data.ticker}</h3>
          <p>
            Текущая цена: ~{data.history?.prices?.slice(-1)[0]?.toFixed(2) || "—"}
          </p>
          <p>
            Прогноз на {horizon} дн.: ~{data.forecast?.prices?.slice(-1)[0]?.toFixed(2) || "—"}
          </p>

          {/* Простая текстовая визуализация графика */}
          <div style={{
            fontFamily: "monospace",
            background: "#f5f5f5",
            padding: "10px",
            borderRadius: "4px",
            whiteSpace: "pre",
            overflowX: "auto",
          }}>
            {renderSimpleChart(data)}
          </div>
        </div>
      )}
    </div>
  );
}

function renderSimpleChart(data: any): string {
  if (!data?.history?.prices || !data?.forecast?.prices) return "Нет данных";

  const allPrices = [...data.history.prices, ...data.forecast.prices];
  const max = Math.max(...allPrices);
  const min = Math.min(...allPrices);
  const range = max - min || 1;
  const height = 10;

  const normalize = (v: number) => Math.round(((v - min) / range) * height);

  const historyPart = data.history.prices.map((p: number) => normalize(p));
  const forecastPart = data.forecast.prices.map((p: number) => normalize(p));

  let chart = "";
  for (let row = height; row >= 0; row--) {
    let line = "";
    for (const h of historyPart) {
      line += h >= row ? "█" : " ";
    }
    line += " │ ";
    for (const f of forecastPart) {
      line += f >= row ? "▓" : " ";
    }
    chart += line + "\n";
  }

  chart += "─".repeat(historyPart.length) + "─┼─" + "─".repeat(forecastPart.length) + "\n";
  chart += "История".padEnd(historyPart.length) + "   " + "Прогноз\n";

  return chart;
}

export default Home;