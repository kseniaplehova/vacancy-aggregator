import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext.jsx";
import FavoritesPage from "../favorites-page/favorites-page.jsx";
import Header from "../header/header.jsx";
import MainPage from "../main-page/main-page.jsx";
import ProtectedRoute from "../protected-route/protected-route.jsx";
import { SignIn, SignUp } from "../sign-form/sign-form.jsx";
import VacancyPage from "../vacancy-page/vacancy-page.jsx";
import styles from "./app.module.css";

export default function App() {
  const { user } = useAuth();
  return (
    <div className={styles.app}>
      <Header />
      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<MainPage />} />
          <Route path="/vacancies/:id" element={<VacancyPage />} />
          <Route
            path="/favorites"
            element={
              <ProtectedRoute>
                <FavoritesPage />
              </ProtectedRoute>
            }
          />
          <Route path="/signin" element={user ? <Navigate to="/" replace /> : <SignIn />} />
          <Route path="/signup" element={user ? <Navigate to="/" replace /> : <SignUp />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className={styles.footer}>
        Вакансии собираются автоматически из открытых источников; повторы объединяются.
      </footer>
    </div>
  );
}
