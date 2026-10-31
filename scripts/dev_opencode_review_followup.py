from pathlib import Path

branch_root = Path('.')

# 1) Show an inline explanation for outdated unmanaged installs. Desktop gets its own message;
# other unmanaged installs reuse the existing localized guidance.
apps = Path('src/components/apps/AppsPage.tsx')
text = apps.read_text()
needle = '''  const nodeLine =
    !isVersionLoading && nodeGap ? (
      <p className="flex items-start gap-1 text-caption text-warning-text">
        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        {t("appsPage.updateNeedsNode", {
          version: info?.latest_version,
          required: nodeGap.required,
          current: nodeGap.current,
        })}
      </p>
    ) : null;

  const conflictList =
'''
replacement = '''  const nodeLine =
    !isVersionLoading && nodeGap ? (
      <p className="flex items-start gap-1 text-caption text-warning-text">
        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        {t("appsPage.updateNeedsNode", {
          version: info?.latest_version,
          required: nodeGap.required,
          current: nodeGap.current,
        })}
      </p>
    ) : null;

  const unmanagedLine =
    !isVersionLoading && isOutdated && report?.unmanaged ? (
      <p className="flex items-start gap-1 text-caption text-warning-text">
        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        {defaultInstall?.source === "desktop"
          ? t("settings.toolUpgradeDesktopManagedDetail")
          : t("settings.toolUpgradeUnmanagedDetail", {
              tool: toolDisplayName(tool),
              path: defaultInstall?.path ?? "",
            })}
      </p>
    ) : null;

  const conflictList =
'''
if needle not in text:
    raise SystemExit('AppsPage nodeLine block not found')
text = text.replace(needle, replacement, 1)
needle = '''  const footer =
    wslControls || errorLine || nodeLine || conflictList ? (
      <div className="space-y-2">
        {errorLine}
        {nodeLine}
        {wslControls}
        {conflictList}
      </div>
    ) : undefined;
'''
replacement = '''  const footer =
    wslControls || errorLine || nodeLine || unmanagedLine || conflictList ? (
      <div className="space-y-2">
        {errorLine}
        {nodeLine}
        {unmanagedLine}
        {wslControls}
        {conflictList}
      </div>
    ) : undefined;
'''
if needle not in text:
    raise SystemExit('AppsPage footer block not found')
apps.write_text(text.replace(needle, replacement, 1))

# 2) Add regression coverage for the Desktop-specific explanation and a generic unmanaged install.
tests = Path('tests/components/AppsPage.test.tsx')
text = tests.read_text()
needle = '''    expect(
      card("OpenCode").queryByRole("button", { name: "settings.toolUpdate" }),
    ).toBeNull();

    fireEvent.click(updateAllButton());
'''
replacement = '''    expect(
      card("OpenCode").queryByRole("button", { name: "settings.toolUpdate" }),
    ).toBeNull();
    expect(
      card("OpenCode").getByText("settings.toolUpgradeDesktopManagedDetail"),
    ).toBeInTheDocument();

    fireEvent.click(updateAllButton());
'''
if needle not in text:
    raise SystemExit('Desktop test assertion block not found')
text = text.replace(needle, replacement, 1)
needle = '''  it("withholds the upgrade when the new version needs a newer Node and leaves it out of update all", async () => {
'''
new_test = '''  it("explains why an outdated unmanaged install is skipped", async () => {
    outdated.clear();
    outdated.add("claude");
    mocks.listToolInstallations.mockImplementation(async (tools: string[]) =>
      tools.map((tool) =>
        tool === "claude"
          ? report(tool, { unmanaged: true, command: "", anchored: false })
          : report(tool),
      ),
    );

    await renderApps();
    await waitFor(() =>
      expect(
        card("Claude Code").getByText("settings.toolUpgradeUnmanagedDetail"),
      ).toBeInTheDocument(),
    );
    expect(
      card("Claude Code").queryByRole("button", {
        name: "settings.toolUpdate",
      }),
    ).toBeNull();
  });

  it("withholds the upgrade when the new version needs a newer Node and leaves it out of update all", async () => {
'''
if needle not in text:
    raise SystemExit('AppsPage insertion point not found')
tests.write_text(text.replace(needle, new_test, 1))

# 3) Add a Desktop-managed explanation in every shipped locale.
locale_lines = {
    'src/i18n/locales/en.json': (
        '    "toolUpgradeUnmanagedDetail": "{{tool}} ({{path}}) wasn\'t installed by npm or a recognized installer, so CC Switch can\'t tell how to upgrade it. Upgrade it the way you installed it (e.g. winget, Scoop, or re-running the official install script).",\n',
        '    "toolUpgradeDesktopManagedDetail": "This OpenCode CLI is bundled with OpenCode Desktop and is updated with the Desktop app.",\n',
    ),
    'src/i18n/locales/zh.json': (
        '    "toolUpgradeUnmanagedDetail": "{{tool}}（{{path}}）不是通过 npm 或可识别的安装器安装的，CC Switch 无法判断如何升级它。请用你原来的安装方式升级（例如 winget、Scoop 或重新运行官方安装脚本）。",\n',
        '    "toolUpgradeDesktopManagedDetail": "这个 OpenCode CLI 由 OpenCode Desktop 捆绑提供，并随 Desktop 应用更新。",\n',
    ),
    'src/i18n/locales/zh-TW.json': (
        '    "toolUpgradeUnmanagedDetail": "{{tool}}（{{path}}）不是透過 npm 或可辨識的安裝程式安裝的，CC Switch 無法判斷如何更新它。請使用你原本的安裝方式更新（例如 winget、Scoop 或重新執行官方安裝指令碼）。",\n',
        '    "toolUpgradeDesktopManagedDetail": "這個 OpenCode CLI 由 OpenCode Desktop 隨附，並會隨 Desktop 應用程式一起更新。",\n',
    ),
    'src/i18n/locales/ja.json': (
        '    "toolUpgradeUnmanagedDetail": "{{tool}}（{{path}}）は npm または認識できるインストーラーでインストールされていないため、CC Switch ではアップグレード方法を判断できません。元のインストール方法でアップグレードしてください（例：winget、Scoop、公式インストールスクリプトの再実行）。",\n',
        '    "toolUpgradeDesktopManagedDetail": "この OpenCode CLI は OpenCode Desktop に同梱されており、Desktop アプリと一緒に更新されます。",\n',
    ),
    'src/i18n/locales/tr.json': (
        '    "toolUpgradeUnmanagedDetail": "{{tool}} ({{path}}), npm veya tanınan bir yükleyici tarafından kurulmadığından CC Switch, onu nasıl yükselteceğini söyleyemez. Kurulum şeklinizi yükseltin (örn. Winget, Scoop veya resmi kurulum betiğini yeniden çalıştırın).",\n',
        '    "toolUpgradeDesktopManagedDetail": "Bu OpenCode CLI, OpenCode Desktop ile birlikte gelir ve Desktop uygulamasıyla güncellenir.",\n',
    ),
}
for filename, (old_line, new_line) in locale_lines.items():
    path = Path(filename)
    text = path.read_text()
    if new_line.strip() in text:
        continue
    if old_line not in text:
        raise SystemExit(f'locale anchor not found: {filename}')
    path.write_text(text.replace(old_line, old_line + new_line, 1))

# 4) Make the four primary locale files enforce both unmanaged messages.
locale_test = Path('tests/config/toolManagementLocales.test.ts')
text = locale_test.read_text()
needle = '''  "toolUpgradeConfirmBtn",
  "toolUpgradeUnanchoredHint",
] as const;
'''
replacement = '''  "toolUpgradeConfirmBtn",
  "toolUpgradeUnanchoredHint",
  "toolUpgradeUnmanagedDetail",
  "toolUpgradeDesktopManagedDetail",
] as const;
'''
if needle not in text:
    raise SystemExit('locale coverage insertion point not found')
locale_test.write_text(text.replace(needle, replacement, 1))
