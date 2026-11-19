import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext.jsx";
import { api } from "../../utils/api.js";
import { plural, sourceLabel, vacanciesCount } from "../../utils/format.js";
import PaginationBox from "../pagination-box/pagination-box.jsx";
import SavedSearches from "../saved-searches/saved-searches.jsx";
import VacancyCard from "../vacancy-card/vacancy-card.jsx";
import styles from "./main-page.module.css";

const PAGE_SIZE = 20;

export default function MainPage() {
  // критерии отбора живут в адресе страницы: ссылкой можно поделиться, кнопка «назад» работает
  const [params, setParams] = useSearchParams();
  const filters = {
    q: params.get("q") || "",
    city: params.get("city") || "",
    source: params.get("source") || "",
    has_salary: params.get("has_salary") || "",
  };
  const page = Number(params.get("page")) || 1;

  const { user } = useAuth();
  const [text, setText] = useState(filters.q);
  const [options, setOptions] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.filterOptions().then(setOptions).catch(() => {});
  }, []);

  useEffect(() => setText(filters.q), [filters.q]);

  const key = params.toString();
  useEffect(() => {
    let cancelled = false; // ответ на устаревший запрос не должен затереть свежий
    setLoading(true);
    api
      .vacancies({ ...filters, page })
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setError("");
      })
      .catch((reason) => !cancelled && setError(reason.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
    // после входа или выхода список перезапрашивается: меняются отметки «в избранном»
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, user?.id]);

  function update(changes) {
    const next = { ...filters, ...changes };
    const clean = Object.fromEntries(Object.entries(next).filter(([, value]) => value));
    setParams(clean); // любая смена критериев возвращает на первую страницу
  }

  function goToPage(number) {
    const next = new URLSearchParams(params);
    if (number > 1) next.set("page", number);
    else next.delete("page");
    setParams(next);
    window.scrollTo({ top: 0 });
  }

  const hasFilters = Object.values(filters).some(Boolean);

  return (
    <>
      <form
        className={`card ${styles.filters}`}
        onSubmit={(event) => {
          event.preventDefault();
          update({ q: text.trim() });
        }}
      >
        <div className={styles.search}>
          <input
            type="search"
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Должность, навык или компания"
            aria-label="Слова для поиска"
          />
          <button type="submit" className="button">
            Найти
          </button>
        </div>
        <div className={styles.selects}>
          <select value={filters.city} onChange={(event) => update({ city: event.target.value })} aria-label="Город">
            <option value="">Все города</option>
            {options?.cities.map((item) => (
              <option key={item.value} value={item.value}>
                {item.value} ({item.count})
              </option>
            ))}
          </select>
          <select
            value={filters.source}
            onChange={(event) => update({ source: event.target.value })}
            aria-label="Источник"
          >
            <option value="">Все источники</option>
            {options?.sources.map((item) => (
              <option key={item.value} value={item.value}>
                {sourceLabel(item.value)}
              </option>
            ))}
          </select>
          <label className={styles.checkbox}>
            <input
              type="checkbox"
              checked={filters.has_salary === "true"}
              onChange={(event) => update({ has_salary: event.target.checked ? "true" : "" })}
            />
            С зарплатой
          </label>
          {hasFilters && (
            <button type="button" className={styles.reset} onClick={() => setParams({})}>
              Сбросить
            </button>
          )}
        </div>
      </form>

      <SavedSearches filters={filters} onApply={(search) => update({ ...search, has_salary: "" })} />

      <p className={styles.summary} aria-live="polite">
        {data && (hasFilters ? `Найдено: ${vacanciesCount(data.count)}` : `Всего: ${vacanciesCount(data.count)}`)}
        {options && !hasFilters && options.duplicates_merged > 0 && (
          <span className="muted">
            {" "}
            · {options.duplicates_merged} {plural(options.duplicates_merged, "повтор убран", "повтора убрано", "повторов убрано")}
          </span>
        )}
      </p>

      {error && <p className="error">Не удалось загрузить вакансии: {error}</p>}

      <div className={`${styles.list} ${loading ? styles.loading : ""}`}>
        {data?.results.map((vacancy) => (
          <VacancyCard key={vacancy.id} vacancy={vacancy} />
        ))}
      </div>

      {data && !data.results.length && !error && (
        <div className={`card ${styles.empty}`}>
          <p>По этим критериям вакансий нет.</p>
          <p className="muted">Попробуйте убрать часть слов или выбрать другой город.</p>
        </div>
      )}
      {!data && loading && <p className="muted">Загрузка…</p>}

      {data && <PaginationBox page={page} pages={Math.ceil(data.count / PAGE_SIZE)} onChange={goToPage} />}
    </>
  );
}
