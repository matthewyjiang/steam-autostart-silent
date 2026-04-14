pkgname=steam-autostart-silent
pkgver=1.0.0
pkgrel=1
pkgdesc="Maintain a Steam XDG autostart entry that launches with -silent"
arch=('any')
url="https://example.invalid/steam-autostart-silent"
license=('MIT')
depends=('steam')
install="$pkgname.install"
source=(
  'sync-autostart'
  "$pkgname.hook"
  "$pkgname.install"
)
sha256sums=(
  'SKIP'
  'SKIP'
  'SKIP'
)

package() {
  install -Dm755 sync-autostart "$pkgdir/usr/lib/$pkgname/sync-autostart"
  install -Dm644 "$pkgname.hook" "$pkgdir/usr/share/libalpm/hooks/$pkgname.hook"
}
