"use strict";
var _a;
const ITEMS_PER_PAGE = 24;
const TAG_LIMIT = 6;
const DEFAULT_ENDPOINT = "query";
function getActiveEndpoint() {
    const pathname = window.location.pathname.replace(/^\/+|\/+$/g, "");
    if (pathname in API_ENDPOINTS) {
        return pathname;
    }
    return DEFAULT_ENDPOINT;
}
function createTextBadge(text, className) {
    const badge = document.createElement("span");
    badge.className = className;
    badge.textContent = text;
    return badge;
}
function createMetaLine(text) {
    const line = document.createElement("div");
    line.className = "manga-meta-line";
    line.textContent = text;
    return line;
}
function buildTags(genres) {
    if (!genres || genres.length === 0) {
        return null;
    }
    const tagsWrap = document.createElement("div");
    tagsWrap.className = "tags";
    const visible = genres.slice(0, TAG_LIMIT);
    visible.forEach((genre) => {
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = genre.name;
        tagsWrap.appendChild(tag);
    });
    if (genres.length > TAG_LIMIT) {
        const more = document.createElement("span");
        more.className = "tag tag--more";
        more.textContent = `+${genres.length - TAG_LIMIT}`;
        tagsWrap.appendChild(more);
    }
    return tagsWrap;
}
function buildInfoBlock(manga) {
    var _a, _b, _c, _d;
    const meta = document.createElement("div");
    meta.className = "manga-meta";
    const authorName = (_b = (_a = manga.author) === null || _a === void 0 ? void 0 : _a.name) !== null && _b !== void 0 ? _b : null;
    const languageName = (_d = (_c = manga.language) === null || _c === void 0 ? void 0 : _c.name) !== null && _d !== void 0 ? _d : null;
    if (authorName) {
        meta.appendChild(createMetaLine(authorName));
    }
    const secondLineParts = [];
    if (languageName)
        secondLineParts.push(languageName);
    if (secondLineParts.length > 0) {
        meta.appendChild(createMetaLine(secondLineParts.join(" • ")));
    }
    const badges = document.createElement("div");
    badges.className = "manga-badges";
    if (badges.childElementCount > 0) {
        meta.appendChild(badges);
    }
    return meta;
}
function buildManga(manga) {
    const card = document.createElement("a");
    card.className = "manga";
    card.href = `/manga/${encodeURIComponent(manga.sku)}`;
    card.setAttribute("aria-label", manga.title);
    const cover = document.createElement("div");
    cover.className = "manga-cover";
    const poster = document.createElement("img");
    poster.src = manga.poster;
    poster.alt = manga.title;
    poster.loading = "lazy";
    poster.decoding = "async";
    poster.onerror = () => {
        poster.onerror = null;
        poster.src =
            "data:image/svg+xml;charset=UTF-8," +
                encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 900">
          <rect width="600" height="900" fill="#111827"/>
          <rect x="90" y="120" width="420" height="660" rx="24" fill="#1f2937"/>
          <path d="M180 560l70-85 60 60 70-90 90 115" fill="none" stroke="#64748b" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="250" cy="320" r="40" fill="#64748b"/>
          <text x="300" y="820" text-anchor="middle" fill="#94a3b8" font-family="Arial, sans-serif" font-size="30">No poster</text>
        </svg>
      `);
    };
    cover.appendChild(poster);
    const body = document.createElement("div");
    body.className = "manga-body";
    const title = document.createElement("h2");
    title.className = "manga-title";
    title.textContent = manga.title;
    body.appendChild(title);
    body.appendChild(buildInfoBlock(manga));
    const tags = buildTags(manga.genres);
    if (tags) {
        body.appendChild(tags);
    }
    card.appendChild(cover);
    card.appendChild(body);
    return card;
}
async function buildResponse(endpoint, page, query = null) {
    const baseUrl = API_ENDPOINTS[endpoint];
    const params = new URLSearchParams({
        page: String(page),
        per_page: String(ITEMS_PER_PAGE),
    });
    if (query && query.trim()) {
        params.set("query", query.trim());
    }
    var response;
    if (query) {
        response = await fetch(`${baseUrl}?${params.toString()}`, {
            headers: {
                Accept: "application/json",
            },
        });
    }
    else {
        response = await fetch(`${API_ENDPOINTS['pages']}?${params.toString()}`, {
            headers: {
                Accept: "application/json",
            },
        });
    }
    if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }
    return (await response.json());
}
const gallery = document.getElementById("gallery");
const loader = document.getElementById("loader");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchError = document.getElementById("search-error");
const activeEndpoint = getActiveEndpoint();
const currentUrl = new URL(window.location.href);
const initialQuery = (_a = currentUrl.searchParams.get("query")) !== null && _a !== void 0 ? _a : "";
let currentPage = 1;
let isLoading = false;
let hasMore = true;
let totalItems = 0;
let observer = null;
// --- Topbar hide/show on scroll ---
let topbar = null;
let topbarHeight = 0;
let isTopbarHidden = false;
let lastScrollY = 0;
let scrollTimeout = null;
function updateTopbarHeight() {
    if (!topbar)
        return;
    const newHeight = topbar.offsetHeight;
    if (newHeight > 0 && !isTopbarHidden) {
        topbarHeight = newHeight;
        document.documentElement.style.setProperty('--topbar-height', `${topbarHeight}px`);
    }
    else if (isTopbarHidden) {
        // if hidden, keep variable zero but remember actual height for later
        const actualHeight = topbar.offsetHeight;
        if (actualHeight > 0)
            topbarHeight = actualHeight;
    }
}
function showTopbar() {
    if (!topbar || !isTopbarHidden)
        return;
    topbar.classList.remove('topbar--hidden');
    isTopbarHidden = false;
    document.documentElement.style.setProperty('--topbar-height', `${topbarHeight}px`);
}
function hideTopbar() {
    if (!topbar || isTopbarHidden)
        return;
    topbar.classList.add('topbar--hidden');
    isTopbarHidden = true;
    document.documentElement.style.setProperty('--topbar-height', '0px');
}
function handleScroll() {
    if (scrollTimeout)
        return;
    scrollTimeout = window.requestAnimationFrame(() => {
        const currentScrollY = window.scrollY;
        // only act if scrolled enough (avoid hiding when barely moved)
        const scrollDelta = currentScrollY - lastScrollY;
        if (scrollDelta > 8 && currentScrollY > topbarHeight) {
            // scrolling down
            hideTopbar();
        }
        else if (scrollDelta < -8) {
            // scrolling up
            showTopbar();
        }
        lastScrollY = currentScrollY;
        scrollTimeout = null;
    });
}
function initTopbarBehavior() {
    topbar = document.querySelector('.topbar');
    if (!topbar)
        return;
    updateTopbarHeight();
    window.addEventListener('resize', () => {
        updateTopbarHeight();
        if (!isTopbarHidden) {
            document.documentElement.style.setProperty('--topbar-height', `${topbarHeight}px`);
        }
    });
    window.addEventListener('scroll', handleScroll, { passive: true });
    // initial state
    lastScrollY = window.scrollY;
}
// --- end topbar behavior ---
function setStateMessage(message) {
    if (!gallery)
        return;
    gallery.innerHTML = "";
    const state = document.createElement("div");
    state.className = "gallery-state";
    state.textContent = message;
    gallery.appendChild(state);
}
function setError(message) {
    if (!searchError)
        return;
    searchError.textContent = message;
}
function clearError() {
    setError("");
}
function renderMangas(items) {
    if (!gallery)
        return;
    const fragment = document.createDocumentFragment();
    items.forEach((item) => fragment.appendChild(buildManga(item)));
    gallery.appendChild(fragment);
}
function removeLoader() {
    if (loader) {
        loader.remove();
    }
}
async function loadMore() {
    if (isLoading || !hasMore || !gallery)
        return;
    isLoading = true;
    if (loader) {
        loader.textContent = "Загрузка ещё...";
        loader.style.display = "grid";
    }
    try {
        const result = await buildResponse(activeEndpoint, currentPage, initialQuery);
        if (!result.success) {
            hasMore = false;
            if (currentPage === 1) {
                removeLoader();
                setStateMessage("Ничего не найдено.");
            }
            return;
        }
        if (totalItems === 0) {
            totalItems = result.total;
        }
        if (currentPage === 1) {
            gallery.innerHTML = "";
        }
        if (!result.response.length && currentPage === 1) {
            removeLoader();
            setStateMessage("Ничего не найдено.");
            hasMore = false;
            return;
        }
        renderMangas(result.response);
        const loadedCount = gallery.querySelectorAll(".manga").length;
        if (loadedCount >= totalItems || result.response.length < ITEMS_PER_PAGE) {
            hasMore = false;
            if (loader) {
                loader.textContent = "Это всё";
            }
        }
        else {
            currentPage += 1;
        }
    }
    catch (error) {
        console.error("Ошибка при загрузке:", error);
        if (currentPage === 1) {
            setStateMessage("Не удалось загрузить мангу. Попробуйте ещё раз.");
        }
        hasMore = false;
        if (loader) {
            loader.textContent = "Ошибка загрузки";
        }
    }
    finally {
        isLoading = false;
    }
}
function initInfiniteScroll() {
    if (!loader)
        return;
    observer = new IntersectionObserver((entries) => {
        var _a;
        if ((_a = entries[0]) === null || _a === void 0 ? void 0 : _a.isIntersecting) {
            void loadMore();
        }
    }, {
        root: null,
        rootMargin: "300px 0px",
        threshold: 0.01,
    });
    observer.observe(loader);
}
function initSearch() {
    if (!searchForm || !searchInput)
        return;
    searchInput.value = initialQuery;
    searchForm.addEventListener("submit", (event) => {
        event.preventDefault();
        clearError();
        const value = searchInput.value.trim();
        if (value.length > 120) {
            setError("Слишком длинный запрос.");
            return;
        }
        const nextUrl = new URL(window.location.href);
        nextUrl.pathname = "/query";
        if (value) {
            nextUrl.searchParams.set("query", value);
        }
        else {
            nextUrl.searchParams.delete("query");
        }
        window.location.href = nextUrl.toString();
    });
}
async function main() {
    if (!gallery)
        return;
    initTopbarBehavior();
    initSearch();
    initInfiniteScroll();
    await loadMore();
}
void main();
