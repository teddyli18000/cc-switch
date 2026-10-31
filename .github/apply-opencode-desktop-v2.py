from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one anchor, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


use_tool = "src/components/apps/useToolManagement.ts"
replace_once(
    use_tool,
    '''    const latest = toolManagementState.toolVersionsCache;
    updateToolManagementState({
      toolVersionsCache: {
        data: mergeToolVersions(latest?.data ?? [], current),
        at: Date.now(),
      },
    });''',
    '''    let nextInstallReports = toolManagementState.installReports;
    const outdatedOpenCode = current.find(
      (tool) =>
        tool.name === "opencode" &&
        isUpdateAvailable(tool.version, tool.latest_version),
    );
    if (outdatedOpenCode && !nextInstallReports?.opencode) {
      try {
        const [report] = await settingsApi.listToolInstallations(["opencode"]);
        if (report) {
          nextInstallReports = {
            ...(nextInstallReports ?? {}),
            opencode: report,
          };
        }
      } catch (error) {
        console.error(
          "[useToolManagement] background OpenCode install probe failed",
          error,
        );
        // Probe failure should fall back to the historical UX rather than hiding
        // updates forever. Execution still re-checks the update plan in Rust.
        if (nextInstallReports === null) nextInstallReports = {};
      }
    }

    const latest = toolManagementState.toolVersionsCache;
    updateToolManagementState({
      toolVersionsCache: {
        data: mergeToolVersions(latest?.data ?? [], current),
        at: Date.now(),
      },
      installReports: nextInstallReports,
    });''',
)

replace_once(
    use_tool,
    '''      (tool) =>
        !installReports?.[tool.name as ToolName]?.unmanaged &&
        isUpdateAvailable(tool.version, tool.latest_version),''',
    '''      (tool) =>
        !(tool.name === "opencode" && installReports === null) &&
        !installReports?.[tool.name as ToolName]?.unmanaged &&
        isUpdateAvailable(tool.version, tool.latest_version),''',
)

replace_once(
    use_tool,
    '''          !busyTools.has(toolName) &&
          !loadingTools[toolName] &&
          !installReports?.[toolName]?.unmanaged &&''',
    '''          !busyTools.has(toolName) &&
          !loadingTools[toolName] &&
          !(toolName === "opencode" && installReports === null) &&
          !installReports?.[toolName]?.unmanaged &&''',
)

replace_once(
    use_tool,
    '''      } catch (error) {
        console.error(
          "[useToolManagement] probeToolInstallations failed",
          error,
        );
      }
    },
    [],
  );''',
    '''      } catch (error) {
        console.error(
          "[useToolManagement] probeToolInstallations failed",
          error,
        );
        // Mark the initial probe as finished so an unavailable diagnostics call
        // does not permanently suppress OpenCode's historical upgrade fallback.
        if (toolManagementState.installReports === null) {
          updateToolManagementState({ installReports: {} });
        }
      }
    },
    [],
  );''',
)

apps_page = "src/components/apps/AppsPage.tsx"
replace_once(
    apps_page,
    '''  const isOutdated = isUpdateAvailable(info?.version, info?.latest_version);
  const nodeGap = isOutdated ? info?.update_blocked_by_node : null;
  const broken = Boolean(info?.installed_but_broken);''',
    '''  const isOutdated = isUpdateAvailable(info?.version, info?.latest_version);
  const nodeGap = isOutdated ? info?.update_blocked_by_node : null;
  const waitingForOpenCodeInstallReport =
    tool === "opencode" && tools.installReports === null;
  const broken = Boolean(info?.installed_but_broken);''',
)
replace_once(
    apps_page,
    '''        : isOutdated && !nodeGap && !report?.unmanaged
          ? "update"''',
    '''        : isOutdated &&
            !nodeGap &&
            !waitingForOpenCodeInstallReport &&
            !report?.unmanaged
          ? "update"''',
)


test_file = "tests/components/AppsPage.test.tsx"
anchor = '''  it("does not offer a separate upgrade for OpenCode Desktop's bundled CLI", async () => {'''
test = '''  it("waits for the OpenCode install source before offering an upgrade", async () => {
    outdated.clear();
    outdated.add("opencode");
    const pending = deferred<ToolInstallationReport[]>();
    let requestedTools: string[] = [];
    mocks.listToolInstallations.mockImplementationOnce((tools: string[]) => {
      requestedTools = tools;
      return pending.promise;
    });

    await renderApps();
    await waitFor(() => expect(card("OpenCode").getByText("1.0.0")).toBeInTheDocument());
    expect(
      card("OpenCode").queryByRole("button", { name: "settings.toolUpdate" }),
    ).toBeNull();

    await act(async () => {
      pending.resolve(requestedTools.map((tool) => report(tool)));
      await pending.promise;
    });

    await waitFor(() => expect(updateButton("OpenCode")).toBeEnabled());
  });

  it("does not advertise a Desktop-managed OpenCode update from the background check", async () => {
    outdated.clear();
    outdated.add("opencode");
    mocks.listToolInstallations.mockImplementation(async (tools: string[]) =>
      tools.map((tool) =>
        report(tool, {
          unmanaged: tool === "opencode",
          command: tool === "opencode" ? "" : `${tool} update`,
        }),
      ),
    );

    const { checkToolUpdatesInBackground, useToolUpdatesAvailable } =
      await import("@/components/apps/useToolManagement");
    await act(async () => {
      await checkToolUpdatesInBackground();
    });

    function UpdateIndicator() {
      return <span data-testid="updates-available">{String(useToolUpdatesAvailable())}</span>;
    }
    render(<UpdateIndicator />);

    expect(screen.getByTestId("updates-available")).toHaveTextContent("false");
    expect(mocks.listToolInstallations).toHaveBeenCalledWith(["opencode"]);
  });

'''
replace_once(test_file, anchor, test + anchor)
