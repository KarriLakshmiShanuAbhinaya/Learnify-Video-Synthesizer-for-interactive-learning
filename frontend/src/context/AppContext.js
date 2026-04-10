import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [query, setQuery] = useState("");
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState("");
  const [user, setUser] = useState(() => localStorage.getItem("username"));
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const login = (username) => {
    setUser(username);
  };

  const logout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("username");
    localStorage.removeItem("email");
    localStorage.removeItem("token");
    setUser(null);
  };

  const value = useMemo(
    () => ({
      query,
      setQuery,
      videos,
      setVideos,
      error,
      setError,
      user,
      setUser,
      theme,
      setTheme,
      toggleTheme,
      login,
      logout,
    }),
    [query, videos, error, user, theme]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
}
