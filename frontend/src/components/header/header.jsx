import { Link, NavLink } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext.jsx";
import styles from "./header.module.css";

export default function Header() {
  const { user, signOut } = useAuth();
  const linkClass = ({ isActive }) => (isActive ? `${styles.link} ${styles.active}` : styles.link);
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link to="/" className={styles.logo}>
          Вакансии<span className={styles.logoAccent}>.без повторов</span>
        </Link>
        <nav className={styles.nav}>
          <NavLink to="/" end className={linkClass}>
            Все
          </NavLink>
          {user && (
            <NavLink to="/favorites" className={linkClass}>
              Избранное
            </NavLink>
          )}
        </nav>
        <div className={styles.account}>
          {user ? (
            <>
              <span className={styles.user} title={user.email}>
                {user.username}
              </span>
              <button type="button" className="button button-secondary" onClick={signOut}>
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link to="/signin" className="button button-secondary">
                Войти
              </Link>
              <Link to="/signup" className={`button ${styles.signup}`}>
                Регистрация
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
