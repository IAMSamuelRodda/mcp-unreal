# unreal-foo

First-playable UE 5.8 + MCP experiment. Canonical scripts and Foo project config live in **[unreal-foo](https://github.com/iamsamuelrodda/unreal-foo)** (or `~/repos/unreal-foo`).

After changing structured tools here, coordinate with unreal-foo docs in `docs/HANDOFF.md` and `../unreal-foo/tools/README.md`.

## v0.4 Foo tools

| Tool | Purpose |
| --- | --- |
| `ue_foo_showcase` | Runs `foo_showcase.setup_showcase()` in the live Foo editor project. |
| `ue_foo_asset_foundation` | Creates `/Game/Foo` folders, `LV_FooArena`, and first Blueprint/UMG asset shells. |
| `ue_list_actors` | Lists actors in the current editor level, optionally filtered by label prefix. |
| `ue_screenshot` | Requests a high-resolution viewport screenshot under `<UE_WORK_ROOT>/screenshots/` on the editor host by default. |

Run after syncing `~/repos/unreal-foo/scripts` into `<UE_WORK_ROOT>/scripts` (`H:\UnrealWork\scripts` on win11-gpu; see README → "Windows editor over SSH").
