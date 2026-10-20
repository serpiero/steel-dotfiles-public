.pragma library

// Inject before the document is painted; CSS also covers nodes added by SPA navigation.
function script(options) {
    return `(() => {
        const options = ${JSON.stringify(options)};
        const host = new URL(options.url).hostname;
        const compact = options.theme === 'compact-forum' && location.hostname === host;
        let observer;
        const css = [
            'html{color-scheme:dark!important;scrollbar-width:none!important;}',
            '*::-webkit-scrollbar{width:0!important;height:0!important;display:none!important;}',
            location.hostname === host ? [
                ':root,.dark,[data-theme="dark"]{'+
                '--main-surface-primary:'+options.background+'!important;--main-surface-secondary:'+options.background+'!important;'+
                '--main-surface-tertiary:'+options.separator+'!important;--sidebar-surface-primary:'+options.background+'!important;'+
                '--sidebar-surface-secondary:'+options.separator+'!important;--bg-primary:'+options.background+'!important;'+
                '--bg-secondary:'+options.background+'!important;--bg-tertiary:'+options.separator+'!important;'+
                '--text-primary:'+(options.text || options.separator)+'!important;--text-secondary:'+(options.muted || options.text || options.separator)+'!important;'+
                '--app-color-background:'+options.background+'!important;--color-surface:'+options.background+'!important;'+
                '--background:'+options.background+'!important;--panel-background:'+options.background+'!important;'+
                '--conversation-panel-background:'+options.background+'!important;--incoming-background:'+options.separator+'!important;'+
                '--outgoing-background:'+options.separator+'!important;--primary:'+(options.text || options.separator)+'!important;'+
                '--secondary:'+(options.muted || options.text || options.separator)+'!important;}',
                'html,body,main,chat-window,bard-sidenav-container{background-color:'+options.background+'!important;color:'+(options.text || options.separator)+'!important;}',
                '::selection{background:'+options.separator+'!important;}',
            ].join('') : '',
            compact ? [
                'html,body,#wrap,main{background:'+options.background+'!important;background-image:none!important;min-width:0!important;box-sizing:border-box!important;}',
                'header.page,.calendar,.topost,.audiosex,.ReqFeed,.welcome,.MainSRC,.post article aside.rls{display:none!important;}',
                'main{flex:1 1 0%!important;padding:12px 6px 0!important;max-width:100%!important;}',
                '#fresh,#archive,#PostComWrap,#inside,.post{width:100%!important;max-width:100%!important;min-width:0!important;margin-left:0!important;margin-right:0!important;box-sizing:border-box!important;}',
                'article,section,header,footer,.post,.feed,.feed a,.neon,input[type=search],input[type=text],nav#menu,.post h1,.post h2,.post h3,.post h3 span,.post .subtitle,.post .RlsContainer{background-color:'+options.background+'!important;background-image:none!important;}',
                'html,body,#wrap,main,#fresh,#archive,section,article,form,.neon,nav#menu,.thumbnail,.highslide,.post img,input[type=search],input[type=text]{border:0!important;outline:0!important;box-shadow:none!important;text-shadow:none!important;border-image:none!important;}',
                '.post article,.post section.descr{overflow-wrap:anywhere!important;}',
                '#fresh article::after,#archive article::after,.inPoll::after,.src_mess::after{background:none!important;}',
                '#fresh article::after,#archive article::after{height:0!important;margin:0!important;}',
                '.post a.permalink,.post h1,.post h2{background:transparent!important;border:0!important;outline:0!important;box-shadow:none!important;text-shadow:none!important;}',
                '#fresh>article+article,#archive>article+article{border-top:2px solid '+options.separator+'!important;margin-top:24px!important;padding-top:24px!important;}',
                '.post img{max-width:100%!important;height:auto!important;}'
            ].join('') : ''
        ].join('');
        const apply = () => {
            const html = document.documentElement;
            if (!html) return;
            html.style.setProperty('color-scheme','dark','important');
            if (options.id === 'chatgpt' && location.hostname === host) {
                try { localStorage.setItem('theme','dark'); } catch (_) {}
                html.classList.add('dark'); html.classList.remove('light');
            }
            let style = document.getElementById('steel-intelligence-theme');
            if (!style) {
                style = document.createElement('style'); style.id = 'steel-intelligence-theme';
                (document.head || html).appendChild(style);
            }
            if (style.textContent !== css) style.textContent = css;
            window.__steelIntelligenceReady = true;
        };
        if (window.__steelIntelligenceObserver) window.__steelIntelligenceObserver.disconnect();
        observer = new MutationObserver(() => {
            // No whole-page scanning or repeated timer: installed CSS handles new content.
            if (!document.getElementById('steel-intelligence-theme')) apply();
        });
        observer.observe(document,{childList:true,subtree:true});
        window.__steelIntelligenceObserver = observer;
        apply();
        const reveal = () => {
            apply();
            console.info('STEEL_INTELLIGENCE_DOCUMENT_READY ' + location.href);
        };
        if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',reveal,{once:true});
        else reveal();
        if (compact && options.lookAhead && !window.__steelLookAhead) {
            window.__steelLookAhead = true;
            let intent, prefetched = false;
            document.addEventListener('pointerover',event => {
                clearTimeout(intent);
                const anchor = event.target.closest && event.target.closest('a[href]');
                if (!anchor || prefetched) return;
                const url = new URL(anchor.href,location.href);
                if (url.hostname !== host || !/^https?:$/.test(url.protocol) || url.href === location.href) return;
                // Anticipate article/category navigation, never account actions or downloads.
                if (!(/\\.html$/.test(url.pathname) || /^\\/page\\/\\d+\\/?$/.test(url.pathname))) return;
                if (url.search || /logout|login|delete/i.test(url.pathname)) return;
                intent = setTimeout(() => {
                    const link = document.createElement('link');link.rel='prefetch';link.as='document';link.href=url.href;
                    (document.head || document.documentElement).appendChild(link);prefetched=true;
                },180);
            },{passive:true});
            document.addEventListener('pointerout',() => clearTimeout(intent),{passive:true});
        }
    })();`;
}
