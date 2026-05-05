import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Favorites from "./pages/Favorites";

function App() {
  return (
    <BrowserRouter>
      <header>
        <h1>🏦 PredictForFSt</h1>
        <nav>
          <Link to="/">Главная</Link>
          <Link to="/login">Войти</Link>
          <Link to="/favorites">Избранное</Link>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/favorites" element={<Favorites />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;