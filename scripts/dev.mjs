import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
const root = process.cwd();
const python =
  process.env.PYTHON_BIN ||
  path.join(
    root,
    ".venv",
    process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
  );
if (!existsSync(python)) {
  console.error(
    "Create .venv and install services/api/requirements.txt first. See LOCAL_DEMO.md.",
  );
  process.exit(1);
}
const children = [];
function launch(command, args, extra = {}) {
  const child = spawn(command, args, {
    stdio: "inherit",
    env: { ...process.env, PYTHONPATH: path.join(root, "services/api") },
    ...extra,
  });
  children.push(child);
  child.on("exit", (code) => {
    if (code) console.error(`Service exited (${code}).`);
  });
}
launch(python, [
  "-m",
  "uvicorn",
  "app.main:app",
  "--host",
  "0.0.0.0",
  "--port",
  "8000",
  "--no-access-log",
]);
launch(python, ["-m", "app.worker"]);
launch(
  process.execPath,
  [
    path.join(root, "node_modules/expo/bin/cli"),
    "start",
    "--web",
    "--port",
    "8081",
  ],
  { cwd: path.join(root, "apps/mobile") },
);
process.on("SIGINT", () => {
  children.forEach((c) => c.kill());
  process.exit();
});
