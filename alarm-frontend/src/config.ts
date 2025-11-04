const API_CONFIG = {
  development: "http://localhost:5502",
  production: "",
};

export const API_URL =
  process.env.REACT_APP_API_URL ||
  API_CONFIG[process.env.NODE_ENV as keyof typeof API_CONFIG] ||
  API_CONFIG.development;

export const CONFIG = {
  API_URL,
  TIMEOUT: 5000,
};

export default CONFIG;
