(function () {
    if (window.__lanStudioCleanUrlsInstalled) return;
    window.__lanStudioCleanUrlsInstalled = true;

    function canonicalPath(pathname) {
        if (pathname === '/home.html') return '/';
        return pathname.replace(/\/index\.html$/i, '/').replace(/\.html$/i, '') || '/';
    }

    function cleanLinks(root = document) {
        if (root.matches?.('a[href]')) cleanLink(root);
        root.querySelectorAll('a[href]').forEach(cleanLink);
    }

    function cleanLink(link) {
        const rawHref = link.getAttribute('href');
        if (!rawHref || rawHref.startsWith('#')) return;

        const url = new URL(rawHref, document.baseURI);
        if (url.origin !== window.location.origin) return;

        const pathname = canonicalPath(url.pathname.replace(/^\/en(?=\/)/i, ''));
        link.setAttribute('href', `${pathname}${url.search}${url.hash}`);
    }

    const cleanPath = canonicalPath(window.location.pathname);
    if (cleanPath !== window.location.pathname) {
        window.history.replaceState(null, '', `${cleanPath}${window.location.search}${window.location.hash}`);
    }

    cleanLinks();
    new MutationObserver((records) => {
        records.forEach(({ addedNodes }) => {
            addedNodes.forEach((node) => {
                if (node.nodeType === Node.ELEMENT_NODE) cleanLinks(node);
            });
        });
    }).observe(document.documentElement, { childList: true, subtree: true });
})();
