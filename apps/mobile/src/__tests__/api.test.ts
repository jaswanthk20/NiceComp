import { api, setToken, onExpired } from "../services/api";
const mockFetch = jest.fn();
global.fetch = mockFetch;
beforeEach(() => {
  mockFetch.mockReset();
  setToken(null);
});
test("sends bearer identity", async () => {
  setToken("test-token");
  mockFetch.mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });
  await api("/me");
  expect(mockFetch.mock.calls[0][1].headers.Authorization).toBe(
    "Bearer test-token",
  );
});
test("explains offline failures", async () => {
  mockFetch.mockRejectedValue(new TypeError("Failed to fetch"));
  await expect(api("/products")).rejects.toThrow("Check your connection");
});
test("clears session on expiry", async () => {
  const expired = jest.fn();
  onExpired(expired);
  mockFetch.mockResolvedValue({
    ok: false,
    status: 401,
    json: async () => ({ detail: "Please sign in." }),
  });
  await expect(api("/me")).rejects.toThrow("Please sign in");
  expect(expired).toHaveBeenCalled();
});
test("preserves actionable server errors", async () => {
  mockFetch.mockResolvedValue({
    ok: false,
    status: 503,
    json: async () => ({ detail: "NICE AI is unavailable." }),
  });
  await expect(api("/chat")).rejects.toThrow("NICE AI is unavailable");
});
