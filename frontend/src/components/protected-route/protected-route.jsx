import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext.jsx";

// Страница только для вошедших: остальных отправляет на вход и запоминает, куда вернуть.
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <p className="muted">Загрузка…</p>;
  if (!user) return <Navigate to="/signin" replace state={{ from: location.pathname }} />;
  return children;
}
