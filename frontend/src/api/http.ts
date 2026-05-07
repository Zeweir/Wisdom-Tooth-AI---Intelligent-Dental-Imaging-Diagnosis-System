import axios from "axios";

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
export const logtoEndpoint =
  import.meta.env.VITE_LOGTO_ENDPOINT ?? "http://127.0.0.1:3001";
export const logtoAppId = import.meta.env.VITE_LOGTO_APP_ID ?? "";
export const logtoApiResource =
  import.meta.env.VITE_LOGTO_API_RESOURCE ??
  "https://api.wisdom-tooth-ai.local";

type AccessTokenProvider = () => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | null = null;

export function setAccessTokenProvider(provider: AccessTokenProvider | null) {
  accessTokenProvider = provider;
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
  if (!accessTokenProvider) {
    return config;
  }

  const token = await accessTokenProvider();
  if (!token) {
    return config;
  }

  config.headers = config.headers ?? {};
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function fetchProtectedBlobUrl(path: string) {
  const resolvedUrl = resolveApiUrl(path);
  const token = accessTokenProvider ? await accessTokenProvider() : null;
  const response = await axios.get<Blob>(resolvedUrl, {
    responseType: "blob",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return URL.createObjectURL(response.data);
}

export async function fetchProtectedBlob(path: string) {
  const resolvedUrl = resolveApiUrl(path);
  const token = accessTokenProvider ? await accessTokenProvider() : null;
  const response = await axios.get<Blob>(resolvedUrl, {
    responseType: "blob",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return response.data;
}
