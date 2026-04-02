const CONFIG = {
    // LOCAL DEV: points to your local FastAPI server
    API_BASE_URL: "http://localhost:5000",
    // PRODUCTION: uncomment below and comment above when deploying
    // API_BASE_URL: "https://learnify-backend-c7nr.onrender.com",
};

export const fetchAuth = async (url, options = {}) => {
    const token = localStorage.getItem("token");
    const headers = {
        ...options.headers,
    };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
        localStorage.removeItem("user");
        localStorage.removeItem("username");
        localStorage.removeItem("email");
        localStorage.removeItem("token");
        window.location.href = "/login";
        return new Promise(() => {});
    }
    return res;
};

export default CONFIG;
