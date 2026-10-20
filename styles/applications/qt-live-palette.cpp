// Scoped Qt Widgets adapter. Atomic palette replacement also updates open windows.
#include <QApplication>
#include <QPalette>
#include <QFile>
#include <QFileInfo>
#include <QFileSystemWatcher>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTimer>
#include <dlfcn.h>

static QPalette themed(const QPalette &source);
static const QString menuStyle=QStringLiteral(
    "/* obsidian-context-menu */"
    "QMenu { background: palette(button); color: palette(window-text); border: none; border-radius: 8px; padding: 4px; }"
    "QMenu::item { margin: 0 4px; padding: 6px 20px 6px 10px; border: none; border-radius: 4px; }"
    "QMenu::item:selected { background: palette(highlight); color: palette(highlighted-text); }"
    "QMenu::item:disabled { color: palette(mid); }"
    "QMenu::separator { height: 1px; background: palette(mid); margin: 4px 8px; }");
static void watch_palette() {
    static bool watching=false;if(watching)return;watching=true;
    auto watcher=new QFileSystemWatcher(qGuiApp);
    if(auto app=qobject_cast<QApplication *>(qGuiApp))app->setStyleSheet(app->styleSheet());
    watcher->addPath(QFileInfo(qEnvironmentVariable("OBSIDIAN_NATIVE_PALETTE")).absolutePath());
    auto initialize=reinterpret_cast<void (*)()>(dlsym(RTLD_DEFAULT,"obsidian_editor_initialize"));
    if(initialize)initialize();
    QObject::connect(watcher,&QFileSystemWatcher::directoryChanged,qGuiApp,[] {
        auto next=themed(QGuiApplication::palette());
        if (next!=QGuiApplication::palette()) {
            if(qobject_cast<QApplication *>(qGuiApp)) QApplication::setPalette(next);
            else QGuiApplication::setPalette(next);
            auto editor=reinterpret_cast<void (*)()>(dlsym(RTLD_DEFAULT,"obsidian_editor_refresh"));
            if(editor) editor();
        }
    });
}

void QApplication::setStyleSheet(const QString &source) {
    using Function=void (*)(QApplication *,const QString &);
    static auto original=reinterpret_cast<Function>(dlsym(RTLD_NEXT,"_ZN12QApplication13setStyleSheetERK7QString"));
    if(original)original(this,source.contains(QStringLiteral("/* obsidian-context-menu */"))?source:source+menuStyle);
}

static QPalette themed(const QPalette &source) {
    QFile file(qEnvironmentVariable("OBSIDIAN_NATIVE_PALETTE"));
    if (!file.open(QIODevice::ReadOnly)) return source;
    auto colors=QJsonDocument::fromJson(file.readAll()).object();
    if (!QColor(colors.value("background").toString()).isValid()) return source;
    QPalette result(source);
    struct Role {QPalette::ColorRole role; const char *token;};
    const Role roles[]={{QPalette::Window,"background"},{QPalette::Base,"background"},
      {QPalette::AlternateBase,"low"},{QPalette::WindowText,"text"},{QPalette::Text,"text"},
      {QPalette::Button,"high"},{QPalette::ButtonText,"text"},{QPalette::ToolTipBase,"high"},
      {QPalette::ToolTipText,"text"},{QPalette::Highlight,"selection"},{QPalette::HighlightedText,"text"},
      {QPalette::Link,"accent"},{QPalette::LinkVisited,"accent"},{QPalette::Light,"highest"},
      {QPalette::Midlight,"high"},{QPalette::Mid,"selection"},{QPalette::Dark,"low"},
      {QPalette::Shadow,"background"},{QPalette::BrightText,"text"}};
    for (auto group:{QPalette::Active,QPalette::Inactive,QPalette::Disabled})
      for (auto role:roles) {
        const bool disabled=group==QPalette::Disabled && (role.role==QPalette::WindowText ||
           role.role==QPalette::Text || role.role==QPalette::ButtonText);
        result.setColor(group,role.role,QColor(colors.value(disabled?"muted":role.token).toString()));
      }
    return result;
}

void QApplication::setPalette(const QPalette &source,const char *className) {
    using Function=void (*)(const QPalette &,const char *);
    static auto original=reinterpret_cast<Function>(dlsym(RTLD_NEXT,"_ZN12QApplication10setPaletteERK8QPalettePKc"));
    if (original) original(themed(source),className);
}

void QGuiApplication::setPalette(const QPalette &source) {
    using Function=void (*)(const QPalette &);
    static auto original=reinterpret_cast<Function>(dlsym(RTLD_NEXT,"_ZN15QGuiApplication10setPaletteERK8QPalette"));
    if(original)original(themed(source));
}

extern "C" void obsidian_qapplication(void *,int &,char **,int) asm("_ZN12QApplicationC1ERiPPci");
extern "C" void obsidian_qapplication(void *self,int &argc,char **argv,int flags) {
    using Constructor=void (*)(void *,int &,char **,int);
    auto original=reinterpret_cast<Constructor>(dlsym(RTLD_NEXT,"_ZN12QApplicationC1ERiPPci"));
    original(self,argc,argv,flags);
    QApplication::setPalette(QApplication::palette());
    QTimer::singleShot(0,qApp,watch_palette);
}

extern "C" void obsidian_qguiapplication(void *,int &,char **,int) asm("_ZN15QGuiApplicationC1ERiPPci");
extern "C" void obsidian_qguiapplication(void *self,int &argc,char **argv,int flags) {
    using Constructor=void (*)(void *,int &,char **,int);
    auto original=reinterpret_cast<Constructor>(dlsym(RTLD_NEXT,"_ZN15QGuiApplicationC1ERiPPci"));
    original(self,argc,argv,flags);
    QGuiApplication::setPalette(QGuiApplication::palette());
    QTimer::singleShot(0,qGuiApp,watch_palette);
}
