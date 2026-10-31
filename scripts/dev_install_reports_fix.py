from pathlib import Path

hook = Path("src/components/apps/useToolManagement.ts")
text = hook.read_text()
old = '''    async (options?: { force?: boolean }) => {
      if (!options?.force && toolManagementState.installReports) return;
      try {
'''
new = '''    async (options?: { force?: boolean }) => {
      const currentReports = toolManagementState.installReports;
      const hasCompleteReports =
        currentReports !== null &&
        TOOL_NAMES.every((toolName) => currentReports[toolName] !== undefined);
      if (!options?.force && hasCompleteReports) return;
      try {
'''
if old not in text:
    raise SystemExit("loadInstallations guard not found")
text = text.replace(old, new, 1)
hook.write_text(text)

tests = Path("tests/components/AppsPage.test.tsx")
text = tests.read_text()
needle = '''    expect(mocks.listToolInstallations).toHaveBeenCalledWith(["opencode"]);
  });

  it("does not offer a separate upgrade for OpenCode Desktop's bundled CLI", async () => {
'''
replacement = '''    expect(mocks.listToolInstallations).toHaveBeenCalledWith(["opencode"]);

    mocks.listToolInstallations.mockClear();
    await renderApps();
    await waitFor(() => expect(mocks.listToolInstallations).toHaveBeenCalled());
    expect(
      mocks.listToolInstallations.mock.calls.some(([tools]) => tools.length > 1),
    ).toBe(true);
  });

  it("does not offer a separate upgrade for OpenCode Desktop's bundled CLI", async () => {
'''
if needle not in text:
    raise SystemExit("background install probe test anchor not found")
text = text.replace(needle, replacement, 1)
tests.write_text(text)
