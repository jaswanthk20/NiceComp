export const API =
  process.env.EXPO_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
let accessToken: string | null = null;
let expired: (() => void) | undefined;
export const setToken = (value: string | null) => {
  accessToken = value;
};
export const onExpired = (handler: () => void) => {
  expired = handler;
};

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 150000);
  try {
    const response = await fetch(API + path, {
      ...options,
      signal: controller.signal,
      headers: {
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...(options.body && !(options.body instanceof FormData)
          ? { "Content-Type": "application/json" }
          : {}),
        ...options.headers,
      },
    });
    if (!response.ok) {
      const body = (await response
        .json()
        .catch(() => ({ detail: "Service unavailable. Please retry." }))) as {
        detail?: string;
      };
      if (response.status === 401 && !path.includes("login")) expired?.();
      throw new Error(
        typeof body.detail === "string"
          ? body.detail
          : "Check the fields and try again.",
      );
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof TypeError)
      throw new Error(
        "Cannot reach NICE Support. Check your connection and try again.",
      );
    if (error instanceof Error && error.name === "AbortError")
      throw new Error("The request timed out. Please retry.");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export const post = <T>(path: string, body: unknown) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body) });
