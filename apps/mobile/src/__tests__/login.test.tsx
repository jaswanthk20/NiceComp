import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import { Login } from "../features/auth/Login";
const mockLogin = jest.fn();
jest.mock("../state/auth", () => ({
  useAuth: () => ({
    config: { environment: "development", portable_review: true },
    error: "",
    login: mockLogin,
    retry: jest.fn(),
  }),
}));
jest.mock("@expo/vector-icons", () => ({ Ionicons: "Icon" }));
beforeEach(() => mockLogin.mockReset());
test("requires credentials before submitting", () => {
  const screen = render(<Login />);
  expect(screen.getByRole("button", { name: "Sign in" })).toBeDisabled();
});
test("shows development data disclosure", () => {
  const screen = render(<Login />);
  expect(screen.getByText(/Synthetic customer records/)).toBeTruthy();
});
test("submits email and password", async () => {
  mockLogin.mockResolvedValue(undefined);
  const screen = render(<Login />);
  fireEvent.changeText(
    screen.getByLabelText("Email address"),
    "customer@nicecomp.test",
  );
  fireEvent.changeText(screen.getByLabelText("Password"), "Review-Only-2026!");
  fireEvent.press(screen.getByRole("button", { name: "Sign in" }));
  await waitFor(() =>
    expect(mockLogin).toHaveBeenCalledWith(
      "customer@nicecomp.test",
      "Review-Only-2026!",
    ),
  );
});
test("shows sign-in errors", async () => {
  mockLogin.mockRejectedValue(new Error("Invalid credentials"));
  const screen = render(<Login />);
  fireEvent.changeText(
    screen.getByLabelText("Email address"),
    "test@example.test",
  );
  fireEvent.changeText(screen.getByLabelText("Password"), "wrong");
  fireEvent.press(screen.getByRole("button", { name: "Sign in" }));
  await waitFor(() =>
    expect(screen.getByText("Invalid credentials")).toBeTruthy(),
  );
});
