import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext.jsx";
import styles from "./sign-form.module.css";

function SignForm({ title, fields, submitLabel, onSubmit, footer }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [values, setValues] = useState(Object.fromEntries(fields.map((field) => [field.name, ""])));
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onSubmit(values);
      navigate(location.state?.from || "/", { replace: true });
    } catch (reason) {
      setError(reason.status === 401 ? "Неверное имя пользователя или пароль." : reason.message);
      setBusy(false);
    }
  }

  return (
    <form className={`card ${styles.form}`} onSubmit={handleSubmit}>
      <h1 className={styles.title}>{title}</h1>
      {fields.map((field) => (
        <label key={field.name} className={styles.field}>
          <span>{field.label}</span>
          <input
            name={field.name}
            type={field.type || "text"}
            autoComplete={field.autoComplete}
            value={values[field.name]}
            onChange={(event) => setValues({ ...values, [field.name]: event.target.value })}
            required
          />
          {field.hint && <small className="muted">{field.hint}</small>}
        </label>
      ))}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <button type="submit" className="button" disabled={busy}>
        {busy ? "Подождите…" : submitLabel}
      </button>
      <p className={styles.footer}>{footer}</p>
    </form>
  );
}

export function SignIn() {
  const { signIn } = useAuth();
  const location = useLocation();
  return (
    <SignForm
      title="Вход"
      submitLabel="Войти"
      fields={[
        { name: "username", label: "Имя пользователя", autoComplete: "username" },
        { name: "password", label: "Пароль", type: "password", autoComplete: "current-password" },
      ]}
      onSubmit={({ username, password }) => signIn(username.trim(), password)}
      footer={
        <>
          Ещё нет аккаунта?{" "}
          <Link to="/signup" state={location.state}>
            Зарегистрироваться
          </Link>
        </>
      }
    />
  );
}

export function SignUp() {
  const { signUp } = useAuth();
  const location = useLocation();
  return (
    <SignForm
      title="Регистрация"
      submitLabel="Зарегистрироваться"
      fields={[
        { name: "username", label: "Имя пользователя", autoComplete: "username" },
        { name: "email", label: "Электронная почта", type: "email", autoComplete: "email" },
        {
          name: "password",
          label: "Пароль",
          type: "password",
          autoComplete: "new-password",
          hint: "Не короче 8 символов, не только цифры",
        },
      ]}
      onSubmit={({ username, email, password }) => signUp(username.trim(), email.trim(), password)}
      footer={
        <>
          Уже есть аккаунт?{" "}
          <Link to="/signin" state={location.state}>
            Войти
          </Link>
        </>
      }
    />
  );
}
