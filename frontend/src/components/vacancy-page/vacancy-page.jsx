import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../../utils/api.js";
import { seenAgo, sourceLabel } from "../../utils/format.js";
import FavoriteButton from "../favorite-button/favorite-button.jsx";
import { SourceLinks } from "../vacancy-card/vacancy-card.jsx";
import styles from "./vacancy-page.module.css";

export default function VacancyPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [vacancy, setVacancy] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setVacancy(null);
    setError("");
    api
      .vacancy(id)
      .then(setVacancy)
      .catch((reason) => setError(reason.status === 404 ? "Такой вакансии нет: возможно, она объединена с другой." : reason.message));
  }, [id]);

  if (error) {
    return (
      <div className={`card ${styles.page}`}>
        <p className="error">{error}</p>
        <Link to="/">← Ко всем вакансиям</Link>
      </div>
    );
  }
  if (!vacancy) return <p className="muted">Загрузка…</p>;

  const main = vacancy.sources[0];
  return (
    <article className={`card ${styles.page}`}>
      <button type="button" className={styles.back} onClick={() => (window.history.length > 1 ? navigate(-1) : navigate("/"))}>
        ← Назад к списку
      </button>
      <h1 className={styles.title}>{vacancy.title}</h1>
      <p className={styles.meta}>
        {[vacancy.company, vacancy.city].filter(Boolean).join(" · ") || "Компания не указана"}
      </p>
      {vacancy.salary && <p className={styles.salary}>{vacancy.salary}</p>}

      <div className={styles.actions}>
        <a href={main.url} target="_blank" rel="noopener noreferrer" className="button">
          Открыть на {sourceLabel(main.source)}
        </a>
        <FavoriteButton vacancyId={vacancy.id} initial={vacancy.is_favorite} withLabel />
      </div>

      <section className={styles.section}>
        <h2 className={styles.heading}>Где опубликована</h2>
        <SourceLinks sources={vacancy.sources} />
      </section>

      <section className={styles.section}>
        <h2 className={styles.heading}>Описание</h2>
        {vacancy.description ? (
          <p className={styles.description}>{vacancy.description}</p>
        ) : (
          <p className="muted">Источник не дал описания — откройте вакансию на исходной площадке.</p>
        )}
      </section>

      <p className={`muted ${styles.seen}`}>Добавлена в сервис {seenAgo(vacancy.first_seen)}</p>
    </article>
  );
}
