const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, { headers: { 'Content-Type':'application/json', ...(options.headers || {}) }, ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data?.error?.message || `Request failed (${response.status})`);
  return data;
}
