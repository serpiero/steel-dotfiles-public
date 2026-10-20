/* Attach only the local display stylesheet; no navigation, account or script changes. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <webkit2/webkit2.h>

typedef struct {WebKitUserContentManager *manager;WebKitUserStyleSheet *sheet;GFileMonitor *monitor;} Style;
static void reload_style(Style *style) {
    const char *path=getenv("OBSIDIAN_WEBKIT_CSS");
    if (!path || !style->manager) return;
    FILE *file=fopen(path,"rb"); if (!file) return;
    fseek(file,0,SEEK_END); long size=ftell(file); rewind(file);
    if (size<0 || size>1048576) {fclose(file); return;}
    char *css=calloc((size_t)size+1,1);
    if (!css) {fclose(file); return;}
    if (fread(css,1,(size_t)size,file)!=(size_t)size) {free(css); fclose(file);return;}
    fclose(file);
    WebKitUserStyleSheet *sheet=webkit_user_style_sheet_new(css,
        WEBKIT_USER_CONTENT_INJECT_TOP_FRAME,WEBKIT_USER_STYLE_LEVEL_USER,NULL,NULL);
    webkit_user_content_manager_add_style_sheet(style->manager,sheet);
    if (style->sheet) {
        webkit_user_content_manager_remove_style_sheet(style->manager,style->sheet);
        webkit_user_style_sheet_unref(style->sheet);
    }
    style->sheet=sheet;free(css);
}
static void file_changed(GFileMonitor *monitor,GFile *file,GFile *other,GFileMonitorEvent event,gpointer data) {
    char *name=g_file_get_basename(file);
    if (g_strcmp0(name,"webkit.css")==0) reload_style(data);
    g_free(name);
}
static void destroy_style(gpointer data) {
    Style *style=data;
    if(style->monitor) {
        g_signal_handlers_disconnect_by_data(style->monitor,style);
        g_file_monitor_cancel(style->monitor);
        g_object_unref(style->monitor);
    }
    if(style->sheet)webkit_user_style_sheet_unref(style->sheet);
    free(style);
}
static void apply_style(WebKitUserContentManager *manager) {
    const char *path=getenv("OBSIDIAN_WEBKIT_CSS");
    if(!path || !manager || g_object_get_data(G_OBJECT(manager),"obsidian-steel"))return;
    Style *style=calloc(1,sizeof(*style));style->manager=manager;
    reload_style(style);
    char *directory=g_path_get_dirname(path);GFile *folder=g_file_new_for_path(directory);
    style->monitor=g_file_monitor_directory(folder,G_FILE_MONITOR_NONE,NULL,NULL);
    if(style->monitor)g_signal_connect(style->monitor,"changed",G_CALLBACK(file_changed),style);
    g_object_unref(folder);g_free(directory);
    g_object_set_data_full(G_OBJECT(manager),"obsidian-steel",style,destroy_style);
}

WebKitUserContentManager *webkit_user_content_manager_new(void) {
    WebKitUserContentManager *(*original)(void)=dlsym(RTLD_NEXT,"webkit_user_content_manager_new");
    if (!original) return NULL;
    WebKitUserContentManager *manager=original();apply_style(manager);return manager;
}

WebKitUserContentManager *webkit_web_view_get_user_content_manager(WebKitWebView *view) {
    WebKitUserContentManager *(*original)(WebKitWebView *)=dlsym(RTLD_NEXT,"webkit_web_view_get_user_content_manager");
    if (!original) return NULL;
    WebKitUserContentManager *manager=original(view);apply_style(manager);return manager;
}
