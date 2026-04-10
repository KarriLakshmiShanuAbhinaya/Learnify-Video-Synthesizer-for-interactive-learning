import React from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import "./styles.css";

// Components
import Navbar from "./components/Navbar";
import { Toaster } from "react-hot-toast";

// Pages
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import SearchPage from "./pages/SearchPage";
import HistoryPage from "./pages/HistoryPage";
import TranscriptPage from "./pages/TranscriptPage";
import SummaryPage from "./pages/SummaryPage";
import CodePracticePage from "./pages/CodePracticePage";
import { useAppContext } from "./context/AppContext";

function App() {
  const {
    query,
    setQuery,
    videos,
    setVideos,
    error,
    setError,
    user,
    theme,
    toggleTheme,
    login,
    logout,
  } = useAppContext();

  return (
    <Router>
      <Toaster position="top-right" />
      <Navbar user={user} onLogout={logout} theme={theme} toggleTheme={toggleTheme} />
      <main className="container">
        <Routes>
          <Route path="/login" element={<LoginPage setUser={login} />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<ProtectedRoute user={user}><SearchPage query={query} setQuery={setQuery} videos={videos} setVideos={setVideos} error={error} setError={setError} /></ProtectedRoute>} />
          <Route path="/transcript/:videoId" element={<ProtectedRoute user={user}><TranscriptPage /></ProtectedRoute>} />
          <Route path="/summary" element={<ProtectedRoute user={user}><SummaryPage /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute user={user}><HistoryPage /></ProtectedRoute>} />
          <Route path="/practice" element={<ProtectedRoute user={user}><CodePracticePage /></ProtectedRoute>} />
        </Routes>
      </main>
      <footer className="footer">
        <p>© {new Date().getFullYear()} LEARNIFY — Learn faster with summaries & quizzes</p>
      </footer>
    </Router>
  );
}

function ProtectedRoute({ user, children }) {
  if (!user) return <Navigate to="/login" />;
  return children;
}

export default App;