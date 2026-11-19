import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext.jsx";
import { api } from "../../utils/api.js";
import styles from "./favorite-button.module.css";

export default function FavoriteButton({ vacancyId, initial, onChange, withLabel = false }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [active, setActive] = useState(initial);
  const [busy, setBusy] = useState(false);

  useEffect(() => setActive(initial), [initial]);

  async function toggle() {
    if (!user) {
      navigate("/signin", { state: { from: location.pathname + location.search } });
      return;
    }
    setBusy(true);
    const next = !active;
    setActive(next); // сразу показываем результат, при ошибке вернём как было
    try {
      await (next ? api.addFavorite(vacancyId) : api.removeFavorite(vacancyId));
      onChange?.(next);
    } catch {
      setActive(!next);
    } finally {
      setBusy(false);
    }
  }

  const label = active ? "Убрать из избранного" : "В избранное";
  return (
    <button
      type="button"
      className={`${styles.button} ${active ? styles.active : ""}`}
      onClick={toggle}
      disabled={busy}
      aria-pressed={active}
      aria-label={label}
      title={label}
    >
      <span aria-hidden="true">{active ? "★" : "☆"}</span>
      {withLabel && <span className={styles.label}>{active ? "В избранном" : "В избранное"}</span>}
    </button>
  );
}
