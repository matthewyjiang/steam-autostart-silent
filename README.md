# steam-autostart-silent

Arch Linux package that maintains a system-wide Steam XDG autostart entry and ensures Steam launches with the `-silent` flag.

## What it does

- Installs a sync helper at `/usr/lib/steam-autostart-silent/sync-autostart`
- Creates/updates `/etc/xdg/autostart/steam.desktop` from the installed Steam desktop file
- Ensures the autostart `Exec=` command includes `-silent`
- Re-syncs automatically when the `steam` package is installed, upgraded, or removed (via pacman hook)

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

## Remove

```bash
sudo pacman -Rns steam-autostart-silent
```
