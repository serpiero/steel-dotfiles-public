// ==UserScript==
// @name         Steel — RuTracker search
// @namespace    steel.local
// @version      1.1.3
// @description  A quiet search homepage and collapsible native advanced search.
// @match        https://rutracker.org/*
// @run-at       document-start
// @grant        GM_registerMenuCommand
// @grant        GM_addStyle
// @license      GPL-3.0
// ==/UserScript==

(() => {
  'use strict';
  GM_addStyle('html,body,*{scrollbar-width:none!important}*::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}');
  const path = location.pathname;
  const home = path === '/forum/' || path === '/forum/index.php';
  if (!home && path !== '/forum/tracker.php') return;
  window.__steelRuTrackerSearch?.destroy();
  const html = document.documentElement;
  const mode = home ? 'home' : 'results';
  html.dataset.steelRt = mode;
  html.dataset.steelRtAdvanced = 'closed';
  html.dataset.steelRtView = 'closed';
  const style = document.createElement('style');
  style.id = 'steel-rt-style';
  style.className = 'darkreader';
  style.textContent = `
    html[data-steel-rt="home"] #page_container { display: none !important; }
    html[data-steel-rt="results"] #page_header { display: none !important; }
    html[data-steel-rt="results"][data-steel-rt-advanced="closed"] #tr-form { display: none !important; }
    html[data-steel-rt="results"][data-steel-rt-advanced="open"] #tr-form { display: block !important; visibility: visible !important; }
    html[data-steel-rt-legacy-addon][data-steel-rt="home"] #tl-controls { display: none !important; }
    html[data-steel-rt-legacy-addon][data-steel-rt] {
      --tl-primary: #9aacc1 !important;
      --tl-primary-hover: #d6dbe0 !important;
      --tl-primary-pressed: #9aa5b1 !important;
      --tl-primary-soft: #293038 !important;
      --tl-primary-soft-strong: #343b44 !important;
      --tl-surface: #161a1f !important;
      --tl-surface-raised: #293038 !important;
      --tl-border: #343b44 !important;
      --tl-text: #d6dbe0 !important;
      --tl-muted: #9aa5b1 !important;
      --tl-on-primary: #161a1f !important;
      --tl-focus: #9aacc1 !important;
      --tl-shadow: none !important;
      --tl-divider-start: #293038 !important;
      --tl-divider-end: #343b44 !important;
      --tl-divider-text: #d6dbe0 !important;
      --tl-divider-border: #343b44 !important;
      --tl-divider-accent: #9aacc1 !important;
      --tl-search-head-start: #293038 !important;
      --tl-search-head-end: #343b44 !important;
    }
    html[data-steel-rt-legacy-addon][data-steel-rt="results"][data-steel-rt-view="closed"] :is(#tl-controls, .tl-infinite-scroll, #tl-filter-count, #tl-load-progress, #steel-rt-view-extra) { display: none !important; }
    html[data-steel-rt-legacy-addon][data-steel-rt="results"] #tl-toolbar {
      position: relative !important; gap: 10px; padding: 12px !important;
      background: color-mix(in srgb, #293038 35%, transparent) !important;
      border-color: #343b44 !important; color: #d6dbe0 !important;
      box-shadow: none !important;
    }
    html[data-steel-rt-legacy-addon][data-steel-rt="results"] #tl-filter-text {
      flex: 1 1 220px; width: auto !important; max-width: 520px;
      height: 34px; background: transparent !important; color: #d6dbe0 !important;
      border-color: #343b44 !important; border-radius: 18px;
    }
    html[data-steel-rt-legacy-addon][data-steel-rt="results"] #tl-filter-text::placeholder { color: #9aa5b1 !important; }
    html[data-steel-rt-legacy-addon][data-steel-rt] :is(#tl-controls button, #tl-column-picker > summary, #tl-filter-clear, .tl-infinite-scroll, .tl-action-button, .tl-author-stats span, .tl-tag, .tl-added-card) {
      background: #293038 !important; color: #9aacc1 !important;
      border-color: #343b44 !important;
    }
    html[data-steel-rt-legacy-addon][data-steel-rt] #tl-controls button[aria-pressed="true"] {
      background: #343b44 !important; color: #d6dbe0 !important;
      border-color: #9aacc1 !important; box-shadow: none !important;
    }
    html[data-steel-rt-legacy-addon][data-steel-rt] :is(.tl-summary, .tl-author-name, .tl-added-date, .tl-completed-cell) { color: #d6dbe0 !important; }
    html[data-steel-rt-legacy-addon][data-steel-rt] .tl-column-menu { background: #293038 !important; color: #d6dbe0 !important; border-color: #343b44 !important; }
    html[data-steel-rt-legacy-addon][data-steel-rt] #tl-filter-seeded { accent-color: #9aacc1; }
    #steel-rt-view-extra { flex: 1 0 100%; display: flex; flex-wrap: wrap; align-items: center; gap: 12px; padding-top: 12px; border-top: 1px solid #343b44; }
    #steel-rt-view-extra #tl-controls { position: static !important; padding: 0 !important; background: transparent !important; border: 0 !important; box-shadow: none !important; }
    #steel-rt-ui, #steel-rt-ui * { box-sizing: border-box; }
    #steel-rt-ui {
      color: #d6dbe0; font: 15px/1.4 system-ui, sans-serif;
      width: 100%; background: transparent; margin: 0;
    }
    #steel-rt-ui button[hidden] { display: none !important; }
    #steel-rt-ui[hidden] { display: none !important; }
    #steel-rt-ui .steel-rt-logo { display: block; width: 100%; height: auto; border: 0; }
    #steel-rt-ui .steel-rt-logo-link { display: block; flex: none; }
    html[data-steel-rt="home"] #steel-rt-ui {
      min-height: 100svh; display: flex; flex-direction: column;
      align-items: center; justify-content: center; gap: 28px;
      padding: 32px 24px 16vh;
    }
    html[data-steel-rt="home"] #steel-rt-ui .steel-rt-logo-link { width: min(340px, 76vw); }
    html[data-steel-rt="results"] #steel-rt-ui {
      display: flex; align-items: center; justify-content: center;
      gap: 24px; padding: 22px 24px 26px;
    }
    html[data-steel-rt="results"] #steel-rt-ui .steel-rt-logo-link { width: 170px; }
    #steel-rt-ui form {
      display: flex !important; align-items: center !important; gap: 0;
      width: min(680px, 100%) !important; height: 56px; margin: 0 !important;
      padding: 5px 9px 5px 21px !important; border-radius: 30px;
      border: 1px solid #343b44 !important;
      background: color-mix(in srgb, #293038 50%, transparent) !important;
      box-shadow: none !important;
      transition: border-color .16s ease, background-color .16s ease;
    }
    #steel-rt-ui form:focus-within { border-color: #9aacc1 !important; }
    #steel-rt-ui form:hover { background: color-mix(in srgb, #293038 72%, transparent) !important; }
    #steel-rt-ui input[type="text"] {
      flex: 1 1 0 !important; width: 0 !important; min-width: 0 !important;
      max-width: none !important; height: 42px; padding: 0 !important;
      color: #d6dbe0 !important; background: transparent !important;
      font: 16px/1.4 system-ui, sans-serif !important;
      border: 0 !important; outline: none !important; box-shadow: none !important;
    }
    #steel-rt-ui input[type="text"]::placeholder { color: #9aa5b1 !important; opacity: .8; }
    #steel-rt-ui select { display: none !important; }
    #steel-rt-ui input[type="submit"] {
      appearance: none; flex: 0 0 40px; width: 40px !important; height: 40px;
      margin: 0 !important; padding: 0 !important; border: 0 !important;
      cursor: pointer; font-size: 0 !important; box-shadow: none !important;
      background: #9aacc1 !important;
      mask: url('data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"%3E%3Ccircle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="black" stroke-width="1.8"/%3E%3Cpath d="m16 16 4.5 4.5" stroke="black" stroke-width="1.8" stroke-linecap="round"/%3E%3C/svg%3E') center / 21px 21px no-repeat;
    }
    :is(#steel-rt-advanced-toggle, #steel-rt-view-toggle) {
      flex: none; height: 38px; padding: 0 15px;
      border-radius: 20px; border: 1px solid #343b44;
      color: #9aa5b1; background: transparent;
      font: 13px system-ui, sans-serif; cursor: pointer;
    }
    :is(#steel-rt-advanced-toggle, #steel-rt-view-toggle):hover, :is(#steel-rt-advanced-toggle, #steel-rt-view-toggle):focus-visible {
      color: #d6dbe0; border-color: #9aacc1; outline: none;
    }
    :is(#steel-rt-advanced-toggle, #steel-rt-view-toggle)[aria-expanded="true"] {
      color: #d6dbe0; background: #374453;
    }
    @media (max-width: 1000px) {
      html[data-steel-rt="results"] #steel-rt-ui { flex-wrap: wrap; gap: 16px; }
      html[data-steel-rt="results"] #steel-rt-ui .steel-rt-logo-link { width: 155px; }
      html[data-steel-rt="results"] #steel-rt-ui form { order: 3; width: min(680px, 100%) !important; }
    }
    @media (prefers-reduced-motion: reduce) { #steel-rt-ui form { transition: none; } }
  `;
  html.append(style);
  let form, anchor, ui, button, viewButton, observer, timeout, addonObserver, addonTimeout, rebuildObserver, ready = false, original = false;
  const moved = [], translated = [];
  let addonToolbar;

  function syncToggle() {
    if (!button) return;
    const open = html.dataset.steelRtAdvanced === 'open';
    button.textContent = open ? 'Hide advanced search' : 'Advanced search';
    button.setAttribute('aria-expanded', String(open));
  }

  function setup() {
    if (ready || !document.body) return ready;
    form = document.querySelector('#quick-search, #quick-search-guest');
    const logo = document.querySelector('#logo .site-logo');
    const input = form?.querySelector('input[name="nm"]');
    if (!form || !logo || !input || (!home && !document.querySelector('#tr-form'))) return false;
    ready = true;
    observer?.disconnect(); clearTimeout(timeout);
    anchor = document.createComment('Steel native search position');
    form.before(anchor);
    ui = document.createElement('section');
    ui.id = 'steel-rt-ui'; ui.setAttribute('aria-label', 'RuTracker search');
    const link = document.createElement('a');
    link.href = '/forum/index.php'; link.className = 'steel-rt-logo-link';
    link.setAttribute('aria-label', 'RuTracker home');
    const image = logo.cloneNode(true);
    image.removeAttribute('style'); image.removeAttribute('id');
    image.className = 'steel-rt-logo'; image.alt = 'RuTracker';
    link.append(image); ui.append(link, form);
    input.setAttribute('aria-label', 'Search RuTracker');
    if (!input.placeholder) input.placeholder = 'Search RuTracker';
    const submit = form.querySelector('input[type="submit"]');
    submit?.setAttribute('aria-label', 'Search');
    if (!home) {
      button = document.createElement('button');
      button.id = 'steel-rt-advanced-toggle'; button.type = 'button';
      button.setAttribute('aria-controls', 'tr-form');
      button.addEventListener('click', () => {
        html.dataset.steelRtAdvanced = html.dataset.steelRtAdvanced === 'open' ? 'closed' : 'open';
        syncToggle();
      });
      ui.append(button); syncToggle();
    }
    document.body.prepend(ui);
    translateInterface();
    if (!home) {
      viewButton = document.createElement('button');
      viewButton.id = 'steel-rt-view-toggle'; viewButton.type = 'button';
      viewButton.textContent = 'View options'; viewButton.hidden = true;
      viewButton.setAttribute('aria-controls', 'steel-rt-view-extra');
      viewButton.setAttribute('aria-expanded', 'false');
      viewButton.addEventListener('click', () => {
        const open = html.dataset.steelRtView !== 'open';
        html.dataset.steelRtView = open ? 'open' : 'closed';
        viewButton.setAttribute('aria-expanded', String(open));
        viewButton.textContent = open ? 'Hide view options' : 'View options';
      });
      ui.append(viewButton);
      watchAddon();
    }
    if (original) setOriginalView(true);
    // Reuse the original form, its live listeners, method and hidden fields.
    // Keep original control nodes/listeners; the add-on settings remain its own.
    return true;
  }


  function translateInterface() {
    const words = new Map(Object.entries({
      'Трекер': 'Tracker', 'Страницы': 'Pages', 'След.': 'Next', 'Пред.': 'Previous',
      'Поиск по раздачам': 'Advanced search', 'Перейти к разделу': 'Choose a forum',
      'Упорядочить по': 'Sort by', 'Зарегистрирован': 'Added', 'Название темы': 'Topic title',
      'Количество скачиваний': 'Download count', 'Количество сидов': 'Seeds', 'Количество личей': 'Leeches',
      'Размер': 'Size', 'по возрастанию': 'Ascending', 'по убыванию': 'Descending',
      'Торренты за': 'Date range', 'за все время': 'All time', 'за сегодня': 'Today',
      'последние 3 дня': 'Last 3 days', 'посл. неделю': 'Last week', 'посл. 2 недели': 'Last 2 weeks',
      'последний месяц': 'Last month', 'Показывать только': 'Show only',
      'Только открытые раздачи': 'Open releases only', 'Новые с посл. посещения': 'New since last visit',
      'Скрыть содержимое {...}': 'Hide {...} content', 'Будущие закачки': 'Planned downloads',
      'Автор раздачи': 'Author', 'Мои раздачи': 'My releases', 'Название содержит': 'Title contains',
      'В подразделах': 'Subforums', 'Категории': 'Categories', 'Всех разделах': 'All forums',
      'По форуму': 'Forum search', 'В Google': 'Google', 'Ссылки': 'Links', 'Простой поиск': 'Simple search',
      'Ссылка на выбранные разделы': 'Link to selected forums', 'Помощь по поиску': 'Search help',
      'Все имеющиеся': 'All forums', 'Поиск': 'Search', 'Форум': 'Forum', 'Тема': 'Topic', 'Автор': 'Author', 'Сиды': 'Seeds', 'Личи': 'Leeches', 'Добавлен': 'Added', 'Скачиваний': 'Downloads'
    }));
    const scope = document.querySelector('#main_content_wrap');
    if (!scope) return;
    const walk = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || parent.closest('script, style, #tl-toolbar, #tl-controls') || (parent.closest('#tor-tbl') && !parent.closest('thead'))) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    let node;
    while ((node = walk.nextNode())) {
      const value = node.data.trim().replace(/\s+/g, ' ');
      const next = words.get(value) || (/^Результатов поиска: \d+$/.test(value) ? value.replace('Результатов поиска:', 'Search results:') : null);
      if (next) { translated.push([node, node.data]); node.data = node.data.replace(node.data.trim(), next); }
    }
    const submit = document.querySelector('#tr-submit-btn');
    if (submit && submit.value === 'Поиск') { translated.push([submit, submit.value, 'value']); submit.value = 'Search'; }
    const filter = document.querySelector('#fs-qs-input');
    if (filter) { translated.push([filter, filter.placeholder, 'placeholder']); filter.placeholder = 'Filter forums'; }
  }

  function moveControl(node, parent, before = null) {
    if (!node) return;
    const marker = document.createComment('Steel add-on control position');
    node.before(marker); moved.push([node, marker]); parent.insertBefore(node, before);
  }

  function adaptAddon() {
    const toolbar = document.querySelector('#tl-toolbar');
    const controls = document.querySelector('#tl-controls');
    // VE 2 owns its layout, palette and controls. Only adapt the legacy toolbar.
    if (controls?.matches('details')) {
      addonObserver?.disconnect(); clearTimeout(addonTimeout);
      return true;
    }
    const seeded = document.querySelector('#tl-filter-seeded')?.closest('label');
    const columns = document.querySelector('#tl-column-picker');
    if (!toolbar || !controls || !seeded || !columns) return false;
    if (toolbar === addonToolbar) return true;
    addonToolbar = toolbar;
    html.dataset.steelRtLegacyAddon = 'true';
    viewButton.hidden = false;
    const extra = document.createElement('div'); extra.id = 'steel-rt-view-extra';
    toolbar.append(extra);
    moveControl(columns, toolbar, seeded);
    for (const child of seeded.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) { translated.push([child, child.data]); child.data = ' SO'; }
    }
    seeded.title = 'Seeded only'; seeded.setAttribute('aria-label', 'Seeded only');
    moveControl(controls, extra);
    moveControl(document.querySelector('#tl-infinite-scroll')?.closest('label'), extra);
    moveControl(document.querySelector('#tl-filter-count'), extra);
    moveControl(document.querySelector('#tl-load-progress'), extra);
    addonObserver?.disconnect(); clearTimeout(addonTimeout);
    // Only watch replacement of the add-on toolbar. Idle pages trigger no work.
    rebuildObserver?.disconnect();
    rebuildObserver = new MutationObserver(records => {
      if (records.some(r => [...r.addedNodes].some(n => n.nodeType === 1 && n.id === 'tl-toolbar'))) adaptAddon();
    });
    rebuildObserver.observe(toolbar.parentNode, {childList: true});
    return true;
  }

  function watchAddon() {
    if (adaptAddon()) return;
    addonObserver = new MutationObserver(() => adaptAddon());
    addonObserver.observe(document.querySelector('#main_content_wrap') || document.body, {childList: true, subtree: true});
    addonTimeout = setTimeout(() => addonObserver?.disconnect(), 10000);
  }

  function setOriginalView(value) {
    original = value;
    if (!ready) {
      if (value) delete html.dataset.steelRt;
      return;
    }
    if (value) {
      anchor.after(form); ui.hidden = true; delete html.dataset.steelRt;
    } else {
      ui.querySelector('.steel-rt-logo-link').after(form);
      ui.hidden = false; html.dataset.steelRt = mode;
    }
  }
  function destroy() {
    observer?.disconnect(); clearTimeout(timeout);
    addonObserver?.disconnect(); rebuildObserver?.disconnect(); clearTimeout(addonTimeout);
    for (const [node, marker] of moved.reverse()) { if (marker.isConnected) marker.replaceWith(node); }
    document.querySelector('#steel-rt-view-extra')?.remove();
    for (const [node, text, property = 'data'] of translated) node[property] = text;
    document.removeEventListener('DOMContentLoaded', boot);
    if (anchor && form) anchor.replaceWith(form);
    ui?.remove(); style.remove();
    delete html.dataset.steelRt; delete html.dataset.steelRtAdvanced; delete html.dataset.steelRtView;
    delete html.dataset.steelRtLegacyAddon;
    delete window.__steelRuTrackerSearch;
  }
  function boot() {
    if (setup()) return;
    observer = new MutationObserver(() => { if (setup() && original) setOriginalView(true); });
    observer.observe(document.body || html, {childList: true, subtree: true});
    timeout = setTimeout(() => { if (!ready) destroy(); }, 5000);
  }
  window.__steelRuTrackerSearch = {destroy, setOriginalView};
  if (typeof GM_registerMenuCommand === 'function') {
    GM_registerMenuCommand('Toggle original RuTracker layout', () => setOriginalView(!original));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once: true});
  else boot();
})();
