import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api } from "../utils/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // пока не проверили сохранённый вход, страницы «только для вошедших» не решают, пускать или нет
  const [loading, setLoading] = useState(api.isSignedIn());

  useEffect(() => {
    api.setSignOutHandler(() => setUser(null));
    if (!api.isSignedIn()) return;
    api
      .me()
      .then(setUser)
      .catch(() => api.signOut())
      .finally(() => setLoading(false));
  }, []);

  const signIn = useCallback(async (username, password) => {
    await api.signIn(username, password);
    setUser(await api.me());
  }, []);

  const signUp = useCallback(
    async (username, email, password) => {
      await api.signUp(username, email, password);
      await signIn(username, password);
    },
    [signIn]
  );

  const signOut = useCallback(() => {
    api.signOut();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, signIn, signUp, signOut }), [user, loading, signIn, signUp, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
