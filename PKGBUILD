pkgname=steam-autostart-silent
pkgver=1.1.0
pkgrel=1
pkgdesc="Maintain a Steam XDG autostart entry that launches with -silent"
arch=('any')
url="https://github.com/matthewyjiang/steam-autostart-silent"
license=('MIT')
depends=('gtk4' 'libadwaita' 'polkit' 'python' 'python-gobject' 'steam')
install="$pkgname.install"
source=(
  'sync-autostart'
  'apply-config'
  'steam-autostart-silent-config'
  'steam-autostart-silent-config-app.py'
  'steam-autostart-silent-config.desktop'
  'io.github.matthewyjiang.steam-autostart-silent.policy'
  "$pkgname.hook"
  "$pkgname.install"
)
sha256sums=(
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
)

package() {
  install -Dm755 sync-autostart "$pkgdir/usr/lib/$pkgname/sync-autostart"
  install -Dm755 apply-config "$pkgdir/usr/lib/$pkgname/apply-config"
  install -Dm755 steam-autostart-silent-config "$pkgdir/usr/bin/steam-autostart-silent-config"
  install -Dm644 steam-autostart-silent-config.desktop "$pkgdir/usr/share/applications/steam-autostart-silent-config.desktop"
  install -Dm644 io.github.matthewyjiang.steam-autostart-silent.policy "$pkgdir/usr/share/polkit-1/actions/io.github.matthewyjiang.steam-autostart-silent.policy"
  install -Dm644 steam-autostart-silent-config-app.py "$pkgdir/usr/lib/$pkgname/steam_autostart_silent_config/app.py"
  install -Dm644 "$pkgname.hook" "$pkgdir/usr/share/libalpm/hooks/$pkgname.hook"
}
