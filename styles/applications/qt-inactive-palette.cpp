// qBittorrent custom themes set only the Active palette group. Keep Inactive
// synchronized without changing disabled controls, fonts or widget geometry.
// Loaded only by the qBittorrent launcher; resolve Qt from that application.
#define QT_NO_VERSION_TAGGING
#include <QApplication>
#include <QPalette>
#include <dlfcn.h>

void QApplication::setPalette(const QPalette &source, const char *className)
{
    using SetPalette = void (*)(const QPalette &, const char *);
    static const auto original = reinterpret_cast<SetPalette>(
        dlsym(RTLD_NEXT, "_ZN12QApplication10setPaletteERK8QPalettePKc"));
    if (!original)
        return;
    QPalette palette(source);
    for (int role = 0; role < QPalette::NColorRoles; ++role)
        if (role != QPalette::NoRole)
            palette.setBrush(QPalette::Inactive, QPalette::ColorRole(role),
                             source.brush(QPalette::Active, QPalette::ColorRole(role)));
    original(palette, className);
}
