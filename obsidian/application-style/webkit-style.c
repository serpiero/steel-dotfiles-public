/* Attach only the local display stylesheet; no navigation, account or script changes. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <webkit2/webkit2.h>

static void apply_style(WebKitUserContentManager *manager) {
    const char *path=getenv("OBSIDIAN_WEBKIT_CSS");
    if (!path || !manager || g_object_get_data(G_OBJECT(manager),"obsidian-steel")) return;
    FILE *file=fopen(path,"rb"); if (!file) return;
    fseek(file,0,SEEK_END); long size=ftell(file); rewind(file);
    if (size<0 || size>1048576) {fclose(file); return;}
    char *css=calloc((size_t)size+1,1);
    if (!css) {fclose(file); return;}
    if (fread(css,1,(size_t)size,file)!=(size_t)size) {free(css); fclose(file);return;}
    fclose(file);
    WebKitUserStyleSheet *sheet=webkit_user_style_sheet_new(css,
        WEBKIT_USER_CONTENT_INJECT_TOP_FRAME,WEBKIT_USER_STYLE_LEVEL_USER,NULL,NULL);
    webkit_user_content_manager_add_style_sheet(manager,sheet);
    webkit_user_style_sheet_unref(sheet);free(css);
    g_object_set_data(G_OBJECT(manager),"obsidian-steel",GINT_TO_POINTER(1));
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
