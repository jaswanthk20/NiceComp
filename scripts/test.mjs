import { spawnSync } from "node:child_process";
import path from "node:path";
const python =
  process.env.PYTHON_BIN ||
  path.join(
    process.cwd(),
    ".venv",
    process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
  );
const result = spawnSync(python, ["-m", "pytest", "tests/backend", "-q"], {
  stdio: "inherit",
  env: { ...process.env, PYTHONPATH: path.join(process.cwd(), "services/api") },
});
process.exit(result.status ?? 1);
