const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");

function walkFiles(directory) {
  const entries = fs.readdirSync(directory, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return walkFiles(fullPath);
    return fullPath;
  });
}

test("package exposes reproducible setup and backend test commands", () => {
  const packageJson = JSON.parse(
    fs.readFileSync(path.join(root, "package.json"), "utf8")
  );

  assert.equal(packageJson.scripts.setup, "bash scripts/bootstrap.sh");
  assert.equal(packageJson.scripts["backend:test"], "bash scripts/run_backend_tests.sh");
  assert.equal(packageJson.scripts.verify, "npm test && npm run backend:test");
});

test("README describes the current real JD state and bootstrap flow", () => {
  const readme = fs.readFileSync(path.join(root, "README.md"), "utf8");

  assert.match(readme, /148 条 BOSS JD/);
  assert.match(readme, /npm run setup/);
  assert.doesNotMatch(readme, /Current JD records are manual seed samples/);
});

test("formal project root does not expose obsolete static entry files", () => {
  for (const fileName of ["index.html", "script.js", "styles.css"]) {
    assert.equal(
      fs.existsSync(path.join(root, fileName)),
      false,
      `${fileName} should not live at the formal project root`
    );
  }
});

test("generated backup files are not left in active source paths", () => {
  const backupFiles = walkFiles(root).filter((filePath) =>
    /\.backup-|\.backup\./.test(path.basename(filePath))
  );

  assert.deepEqual(backupFiles, []);
});

test("result page has a stable confidence display target", () => {
  const html = fs.readFileSync(path.join(root, "frontend/index.html"), "utf8");
  const appSource = fs.readFileSync(path.join(root, "frontend/js/app.js"), "utf8");

  assert.match(html, /id="resultConfidence"/);
  assert.match(html, /id="resultExplanation"/);
  assert.match(appSource, /payload\.confidence/);
  assert.match(appSource, /result_explanation/);
});

test("frontend renders detailed action plan fields", () => {
  const appSource = fs.readFileSync(path.join(root, "frontend/js/app.js"), "utf8");

  assert.match(appSource, /day\.goal/);
  assert.match(appSource, /day\.tasks/);
  assert.match(appSource, /day\.deliverable/);
  assert.match(appSource, /day\.resume_sentence/);
  assert.match(appSource, /day\.jd_keywords/);
});

test("quiz keeps auto advance while exposing a manual next button", () => {
  const html = fs.readFileSync(path.join(root, "frontend/index.html"), "utf8");
  const appSource = fs.readFileSync(path.join(root, "frontend/js/app.js"), "utf8");

  assert.match(html, /id="nextBtn"/);
  assert.doesNotMatch(html, /选择后自动进入下一题/);
  assert.match(appSource, /const nextBtn/);
  assert.match(appSource, /ADVANCE_DELAY_MS/);
  assert.match(appSource, /advanceToNext/);
});
