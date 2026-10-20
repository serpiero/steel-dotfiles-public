/* User CSS provider with a directory watch, so atomic writes update existing GTK windows. */
#define _GNU_SOURCE
#include <gtk/gtk.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <string.h>
static GtkCssProvider *provider;
static char *css_path;
static void reload_css(void) {
    const char *path=css_path ? css_path : getenv("OBSIDIAN_GTK_CSS");
    if (!path || !provider) return;
#if GTK_MAJOR_VERSION >= 4
    gtk_css_provider_load_from_path(provider,path);
#else
    gtk_css_provider_load_from_path(provider,path,NULL);
#endif
}
static void changed(GFileMonitor *m,GFile *file,GFile *other,GFileMonitorEvent event,gpointer data) {
    char *name=g_file_get_basename(file);
    if (g_strcmp0(name,"gtk.css")==0) reload_css();
    g_free(name);
}
static void setup(void) {
    const char *path=css_path ? css_path : getenv("OBSIDIAN_GTK_CSS");
    if (provider || !path || !gdk_display_get_default()) return;
    provider=gtk_css_provider_new();reload_css();
#if GTK_MAJOR_VERSION >= 4
    gtk_style_context_add_provider_for_display(gdk_display_get_default(),GTK_STYLE_PROVIDER(provider),GTK_STYLE_PROVIDER_PRIORITY_USER+1);
#else
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),GTK_STYLE_PROVIDER(provider),GTK_STYLE_PROVIDER_PRIORITY_USER+1);
#endif
    char *directory=g_path_get_dirname(path);GFile *folder=g_file_new_for_path(directory);
    GFileMonitor *monitor=g_file_monitor_directory(folder,G_FILE_MONITOR_NONE,NULL,NULL);
    if (monitor) g_signal_connect(monitor,"changed",G_CALLBACK(changed),NULL);
    g_object_unref(folder);g_free(directory);
}
/* Chromium may resolve gtk_init through a library handle, bypassing interposed
 * entry points. Join its GLib loop after its real display has been initialized.
 * Capture our scoped path before a runtime sanitizes its environment. */
static gboolean setup_after_display(gpointer data) {
    static unsigned attempts;
    if (provider) return G_SOURCE_REMOVE;
    if (gdk_display_get_default()) { setup(); return G_SOURCE_REMOVE; }
    return ++attempts < 120 ? G_SOURCE_CONTINUE : G_SOURCE_REMOVE;
}
__attribute__((constructor)) static void capture_scoped_palette(void) {
    const char *path=getenv("OBSIDIAN_GTK_CSS");
    if (!path || !*path) return;
    css_path=strdup(path);
    g_timeout_add(100,setup_after_display,NULL);
}
#if GTK_MAJOR_VERSION >= 4
void gtk_init(void) {void (*original)(void)=dlsym(RTLD_NEXT,"gtk_init");original();setup();}
gboolean gtk_init_check(void) {gboolean (*original)(void)=dlsym(RTLD_NEXT,"gtk_init_check");gboolean ok=original();if(ok)setup();return ok;}
#else
void gtk_init(int *argc,char ***argv) {void (*original)(int *,char ***)=dlsym(RTLD_NEXT,"gtk_init");original(argc,argv);setup();}
gboolean gtk_init_check(int *argc,char ***argv) {gboolean (*original)(int *,char ***)=dlsym(RTLD_NEXT,"gtk_init_check");gboolean ok=original(argc,argv);if(ok)setup();return ok;}
#endif
