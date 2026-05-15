import axios from "axios";

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

export function getStoredToken(): string | null {
  return localStorage.getItem("access_token");
}

export function setStoredToken(token: string | null) {
  if (token) {
    localStorage.setItem("access_token", token);
  } else {
    localStorage.removeItem("access_token");
  }
}

export function resolveApiUrl(path: string) {
  if (!path) {
    return path;
  }
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  if (apiBaseUrl.startsWith("http://") || apiBaseUrl.startsWith("https://")) {
    return `${apiBaseUrl}${path}`;
  }
  return path;
}

export const http = axios.create({
  baseURL: apiBaseUrl,
});

http.interceptors.request.use(async (config) => {
  const token = getStoredToken();
  if (!token) {
    return config;
  }

  config.headers = config.headers ?? {};
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function fetchProtectedBlobUrl(path: string) {
  const resolvedUrl = resolveApiUrl(path);
  const token = getStoredToken();
  const response = await axios.get<Blob>(resolvedUrl, {
    responseType: "blob",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return URL.createObjectURL(response.data);
}

export async function fetchProtectedBlob(path: string) {
  const resolvedUrl = resolveApiUrl(path);
  const token = getStoredToken();
  const response = await axios.get<Blob>(resolvedUrl, {
    responseType: "blob",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return response.data;
}
