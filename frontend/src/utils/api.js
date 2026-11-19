const BASE = "/api/v1";
const STORAGE_KEY = "vacancy-aggregator-tokens";

let tokens = readTokens();
let onSignOut = () => {};

function readTokens() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null;
  } catch {
    return null;
  }
}

function saveTokens(value) {
  tokens = value;
  try {
    if (value) localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
  }
}

export class ApiError extends Error {
  constructor(status, data) {
    super(describe(data) || `Ошибка сервера (${status})`);
    this.status = status;
    this.data = data;
  }
}

function describe(data) {
  if (!data) return "";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  return Object.values(data).flat().join(" ");
}

async function send(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth && tokens?.access) headers.Authorization = `Bearer ${tokens.access}`;
  const response = await fetch(BASE + path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!response.ok) throw new ApiError(response.status, data);
  return data;
}

async function refresh() {
  if (!tokens?.refresh) return false;
  try {
    const data = await send("/auth/jwt/refresh/", { method: "POST", body: { refresh: tokens.refresh }, auth: false });
    saveTokens({ ...tokens, access: data.access });
    return true;
  } catch {
    saveTokens(null);
    onSignOut();
    return false;
  }
}

async function request(path, options = {}) {
  try {
    return await send(path, options);
  } catch (error) {
    const expired = error instanceof ApiError && error.status === 401 && options.auth !== false && tokens;
    if (expired && (await refresh())) return send(path, options);
    throw error;
  }
}

function query(params) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, value);
  });
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  isSignedIn: () => Boolean(tokens),
  setSignOutHandler: (handler) => {
    onSignOut = handler;
  },

  async signIn(username, password) {
    const data = await send("/auth/jwt/create/", { method: "POST", body: { username, password }, auth: false });
    saveTokens(data);
  },
  signUp: (username, email, password) =>
    send("/auth/users/", { method: "POST", body: { username, email, password }, auth: false }),
  signOut: () => saveTokens(null),
  me: () => request("/auth/users/me/"),

  vacancies: (params) => request(`/vacancies/${query(params)}`),
  vacancy: (id) => request(`/vacancies/${id}/`),
  filterOptions: () => request("/filters/", { auth: false }),

  favorites: (page) => request(`/favorites/${query({ page })}`),
  addFavorite: (id) => request(`/vacancies/${id}/favorite/`, { method: "POST" }),
  removeFavorite: (id) => request(`/vacancies/${id}/favorite/`, { method: "DELETE" }),

  searches: () => request("/searches/"),
  createSearch: (search) => request("/searches/", { method: "POST", body: search }),
  deleteSearch: (id) => request(`/searches/${id}/`, { method: "DELETE" }),
};
