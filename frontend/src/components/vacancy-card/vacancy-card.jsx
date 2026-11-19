import { Link } from "react-router-dom";

import { seenAgo, sourceLabel } from "../../utils/format.js";
import FavoriteButton from "../favorite-button/favorite-button.jsx";
import styles from "./vacancy-card.module.css";

export default function VacancyCard({ vacancy, onFavoriteChange }) {
  return (
    <article className={`card ${styles.card}`}>
      <div className={styles.top}>
        <h2 className={styles.title}>
          <Link to={`/vacancies/${vacancy.id}`}>{vacancy.title}</Link>
        </h2>
        <FavoriteButton
          vacancyId={vacancy.id}
          initial={vacancy.is_favorite}
          onChange={(value) => onFavoriteChange?.(vacancy.id, value)}
        />
      </div>
      <p className={styles.meta}>
        {[vacancy.company, vacancy.city].filter(Boolean).join(" · ") || "Компания не указана"}
      </p>
      {vacancy.salary && <p className={styles.salary}>{vacancy.salary}</p>}
      {vacancy.snippet && <p className={styles.snippet}>{vacancy.snippet}</p>}
      <div className={styles.bottom}>
        <SourceLinks sources={vacancy.sources} />
        <span className="muted">добавлена {seenAgo(vacancy.first_seen)}</span>
      </div>
    </article>
  );
}

export function SourceLinks({ sources }) {
  return (
    <ul className={styles.sources} aria-label="Где опубликована">
      {sources.map((item) => (
        <li key={item.url}>
          <a href={item.url} target="_blank" rel="noopener noreferrer" className={styles.source}>
            {sourceLabel(item.source)}
          </a>
        </li>
      ))}
      {sources.length > 1 && <li className={styles.merged}>объединено из {sources.length} источников</li>}
    </ul>
  );
}
