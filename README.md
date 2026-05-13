# steam-autostart-silent

Arch Linux package that maintains a system-wide Steam XDG autostart entry and ensures Steam launches with the `-silent` flag.

Repository: <https://github.com/matthewyjiang/steam-autostart-silent>

## What it does

- Installs a sync helper at `/usr/lib/steam-autostart-silent/sync-autostart`
- Installs a GTK 4 configuration app at `/usr/bin/steam-autostart-silent-config`
- Creates/updates `/etc/xdg/autostart/steam.desktop` from the installed Steam desktop file
- Ensures the autostart `Exec=` command includes `-silent` by default
- Re-syncs automatically when the `steam` package is installed, upgraded, or removed (via pacman hook)

## Configure

Launch the GTK configuration app from your application launcher as **Steam Autostart**, or run:

```bash
steam-autostart-silent-config
```

The app can configure:

- Whether the system-wide Steam autostart entry is enabled
- Whether Steam launches with `-silent`
- Additional Steam launch flags
- Whether the source desktop file is chosen automatically, `steam.desktop`, or `steam-native.desktop`
- Manual re-sync of the managed desktop entry

Changes are written to `/etc/steam-autostart-silent/config.conf` and applied through `pkexec` using the polkit action `io.github.matthewyjiang.steam-autostart-silent.apply`.

Default configuration, used when the config file does not exist:

```ini
ENABLED=true
SILENT=true
EXTRA_FLAGS=""
SOURCE=auto
```

## Install

```bash
makepkg -si
```

## Verify

```bash
grep '^Exec=' /etc/xdg/autostart/steam.desktop
```

Expected: the command contains `-silent`.

## Manual re-sync

```bash
sudo /usr/lib/steam-autostart-silent/sync-autostart
```

## Apply config manually

The GUI uses `/usr/lib/steam-autostart-silent/apply-config` to validate and write config before running `sync-autostart`:

```bash
sudo /usr/lib/steam-autostart-silent/apply-config /path/to/config.conf
```

## Remove

```bash
sudo pacman -Rns steam-autostart-silent
```
