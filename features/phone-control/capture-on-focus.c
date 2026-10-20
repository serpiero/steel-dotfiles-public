/* OTG-only adapter: deterministic SDL3 capture on focus, no event polling. */
#define _GNU_SOURCE
#include <SDL3/SDL.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>

bool SDL_SetWindowRelativeMouseMode(SDL_Window *window, bool enabled) {
    bool (*original)(SDL_Window *, bool) = dlsym(RTLD_NEXT, "SDL_SetWindowRelativeMouseMode");
    if (!original) return false;
    bool ok = original(window, enabled);
    const char *path = getenv("STEEL_PHONE_CAPTURE_STATE");
    if (ok && path) {
        int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
        if (fd >= 0) { char state = enabled ? '1' : '0'; write(fd, &state, 1); close(fd); }
    }
    return ok;
}

bool SDL_WaitEvent(SDL_Event *event) {
    bool (*original)(SDL_Event *) = dlsym(RTLD_NEXT, "SDL_WaitEvent");
    if (!original) return false;
    bool ok = original(event);
    if (ok && event && event->type == SDL_EVENT_WINDOW_FOCUS_GAINED) {
        SDL_Window *window = SDL_GetWindowFromID(event->window.windowID);
        if (window) SDL_SetWindowRelativeMouseMode(window, true);
    }
    return ok;
}
