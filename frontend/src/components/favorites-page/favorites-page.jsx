import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../../utils/api.js";
import { vacanciesCount } from "../../utils/format.js";
import PaginationBox from "../pagination-box/pagination-box.jsx";
import VacancyCard from "../vacancy-card/vacancy-card.jsx";
import styles from "./favorites-page.module.css";

const PAGE_SIZE = 20;

export default function FavoritesPage() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .favorites(page)
      .then((result) => !cancelled && setData(result))
      .catch((reason) => !cancelled && setError(reason.message));
    return () => {
      cancelled = true;
    };
  }, [page]);

  function handleChange(id, isFavorite) {
    if (isFavorite) return;
    setData((current) => ({
      ...current,
      count: current.count - 1,
      results: current.results.filter((vacancy) => vacancy.id !== id),
    }));
  }

  if (error) return <p className="error">Не удалось загрузить избранное: {error}</p>;
  if (!data) return <p className="muted">Загрузка…</p>;

  return (
    <>
      <h1 className={styles.title}>Избранное</h1>
      {data.count > 0 ? (
        <p className={styles.summary}>{vacanciesCount(data.count)}</p>
      ) : (
        <div className={`card ${styles.empty}`}>
          <p>Здесь будут вакансии, которые вы отметите звёздочкой.</p>
          <Link to="/" className="button">
            Смотреть вакансии
          </Link>
        </div>
      )}
      <div className={styles.list}>
        {data.results.map((vacancy) => (
          <VacancyCard key={vacancy.id} vacancy={vacancy} onFavoriteChange={handleChange} />
        ))}
      </div>
      <PaginationBox page={page} pages={Math.ceil(data.count / PAGE_SIZE)} onChange={setPage} />
    </>
  );
}
