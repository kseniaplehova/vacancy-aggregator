import styles from "./pagination-box.module.css";

export default function PaginationBox({ page, pages, onChange }) {
  if (pages <= 1) return null;
  return (
    <nav className={styles.box} aria-label="Страницы">
      <button type="button" className="button button-secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ← Назад
      </button>
      <span className="muted">
        {page} из {pages}
      </span>
      <button
        type="button"
        className="button button-secondary"
        disabled={page >= pages}
        onClick={() => onChange(page + 1)}
      >
        Вперёд →
      </button>
    </nav>
  );
}
