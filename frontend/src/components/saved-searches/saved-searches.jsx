import { useEffect, useState } from "react";

import { useAuth } from "../../contexts/AuthContext.jsx";
import { api } from "../../utils/api.js";
import { sourceLabel } from "../../utils/format.js";
import styles from "./saved-searches.module.css";

// Сохранённые критерии отбора: одним нажатием возвращают нужную выборку вакансий.
export default function SavedSearches({ filters, onApply }) {
  const { user } = useAuth();
  const [searches, setSearches] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) {
      setSearches([]);
      return;
    }
    api.searches().then(setSearches).catch(() => {});
  }, [user]);

  if (!user) return null;

  const current = { query: filters.q, city: filters.city, source: filters.source };
  const canSave = Object.values(current).some(Boolean);
  const same = (search) =>
    search.query === current.query && search.city === current.city && search.source === current.source;
  const alreadySaved = searches.some(same);

  async function save() {
    const name = [current.query, current.city, current.source && sourceLabel(current.source)]
      .filter(Boolean)
      .join(" · ")
      .slice(0, 100);
    try {
      const created = await api.createSearch({ name, ...current });
      setSearches([created, ...searches]);
      setError("");
    } catch (reason) {
      setError(reason.message);
    }
  }

  async function remove(id) {
    try {
      await api.deleteSearch(id);
      setSearches(searches.filter((search) => search.id !== id));
    } catch (reason) {
      setError(reason.message);
    }
  }

  if (!searches.length && !canSave) return null;

  return (
    <section className={styles.box} aria-label="Сохранённые поиски">
      {searches.map((search) => (
        <span key={search.id} className={`${styles.chip} ${same(search) ? styles.active : ""}`}>
          <button
            type="button"
            className={styles.apply}
            onClick={() => onApply({ q: search.query, city: search.city, source: search.source })}
          >
            {search.name}
          </button>
          <button
            type="button"
            className={styles.remove}
            onClick={() => remove(search.id)}
            aria-label={`Удалить поиск «${search.name}»`}
            title="Удалить"
          >
            ×
          </button>
        </span>
      ))}
      {canSave && !alreadySaved && (
        <button type="button" className={styles.save} onClick={save}>
          + Сохранить этот поиск
        </button>
      )}
      {error && <span className={styles.error}>{error}</span>}
    </section>
  );
}
