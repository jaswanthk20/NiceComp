import { test, expect } from "@playwright/test";
import path from "node:path";

test("customer receipt → product documentation → photo ticket → Mailpit → admin", async ({
  page,
  request,
}) => {
  const runtimeErrors: string[] = [];
  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  page.on("console", (message) => {
    if (
      message.type() === "error" &&
      message.text().includes("Unexpected text node")
    )
      runtimeErrors.push(message.text());
  });
  await page.goto("/");
  await page.getByLabel("Email address").fill("customer@nicecomp.test");
  await page.getByLabel("Password", { exact: true }).fill("Review-Only-2026!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByText("Welcome, TEST CUSTOMER", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "docs/screenshots/dashboard-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "My purchases", exact: true }).click();
  await page.getByRole("button", { name: "View purchase details" }).click();
  await expect(page.getByText("Warranty · Active")).toBeVisible();
  await page.getByRole("button", { name: "View receipt", exact: true }).click();
  await expect(page.getByLabel("Receipt page 1")).toBeVisible();
  await page.getByRole("button", { name: "Products", exact: true }).click();
  await page.getByRole("button", { name: "View product", exact: true }).click();
  await expect(
    page.getByText("TEST-SERIAL-001", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Ask NICE AI", exact: true }).click();
  await page
    .getByLabel("Your question", { exact: true })
    .fill("What is the tank capacity?");
  await page
    .getByRole("button", { name: "Send question", exact: true })
    .click();
  await expect(
    page.getByText(/From the documentation for your selected model/).last(),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Source: ECO 10A/ }).last(),
  ).toBeVisible();
  await page.screenshot({
    path: "docs/screenshots/chat-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Issue unresolved? Create ticket" })
    .click();
  await expect(
    page.getByLabel("Problem description", { exact: true }),
  ).toHaveValue("What is the tank capacity?");
  const description = `TEST E2E ${Date.now()}: pressure drop continues; please inspect.`;
  await page
    .getByLabel("Problem description", { exact: true })
    .fill(description);
  await page.getByRole("button", { name: "High", exact: true }).click();
  const chooser = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: "Choose photo", exact: true }).click();
  await (
    await chooser
  ).setFiles(path.resolve("tests/fixtures/test-diagnostic.jpg"));
  await expect(page.getByLabel("Attached diagnostic photo")).toBeVisible();
  await page.getByRole("button", { name: "Submit support ticket" }).click();
  const number = page.getByRole("heading", { name: /NC-\d{4}-/ });
  await expect(number).toBeVisible();
  const ticketNumber = await number.textContent();
  await expect(
    page.getByText("Response target pending company configuration."),
  ).toBeVisible();
  await expect(page.getByLabel("Ticket photo")).toBeVisible();
  await expect
    .poll(
      async () => {
        const result = await request.get(
          "http://127.0.0.1:8025/api/v1/messages",
        );
        const body = await result.json();
        return body.messages.some((m: { Subject: string }) =>
          m.Subject.includes(ticketNumber!),
        );
      },
      { timeout: 30000 },
    )
    .toBeTruthy();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await page.getByLabel("Email address").fill("admin@nicecomp.test");
  await page.getByLabel("Password", { exact: true }).fill("Review-Only-2026!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("button", { name: "Admin", exact: true }).click();
  await expect(page.getByText(description, { exact: true })).toBeVisible();
  await page.screenshot({
    path: "docs/screenshots/admin-desktop.png",
    fullPage: true,
  });
  expect(runtimeErrors).toEqual([]);
});

test("phone viewport retains accessible navigation and sign-in", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByLabel("Email address").fill("customer@nicecomp.test");
  await page.getByLabel("Password", { exact: true }).fill("Review-Only-2026!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByText("Welcome, TEST CUSTOMER")).toBeVisible();
  await page.screenshot({
    path: "docs/screenshots/dashboard-mobile.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Support", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Support tickets", exact: true }),
  ).toBeVisible();
});

test("invalid login remains signed out", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Email address").fill("customer@nicecomp.test");
  await page.getByLabel("Password", { exact: true }).fill("wrong-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByText("Email or password is incorrect.")).toBeVisible();
});
