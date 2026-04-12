"use strict";
// =============================================
// УНИФИЦИРОВАННЫЙ TypeScript — unified-manga.ts
// Объединяет логику главной страницы (index.ts) + страницы манги (manga.ts)
// Единая система фильтрации по тегам (author / genre / language)
// Работает на ОБОИХ страницах без конфликтов
// =============================================
// ==================== КОНСТАНТЫ И ГЛОБАЛЬНОЕ СОСТОЯНИЕ ====================
const ITEMS_PER_PAGE = 24;
const TAG_LIMIT = 6;
let randomTag = {
    endpoint: "pages",
    query: "",
    displayText: "Новинки",
};
let activeEndpoint = "pages";
let initialQuery = "";
let currentPage = 1;
let isLoading = false;
let hasMore = true;
let totalItems = 0;
let observer = null;
// DOM-элементы (общие для обеих страниц)
const galleryEl = document.getElementById("gallery");
const loaderEl = document.getElementById("loader");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchError = document.getElementById("search-error");
const textShowEl = document.getElementById("textShow");
// ==================== УТИЛИТЫ ====================
// Ключевые изменения: добавлена детекция страницы + getSkuFromUrl
function isDetailPage() {
    return window.location.pathname.startsWith("/manga/");
}
function getSkuFromUrl() {
    const pathname = window.location.pathname.replace(/^\/+|\/+$/g, "");
    const parts = pathname.split("/");
    return parts[parts.length - 1] || null;
}
// ==================== BUILDERS ДЛЯ КАРТОЧЕК (из index.ts) ====================
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
    if (!genres || genres.length === 0)
        return null;
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
    if (authorName)
        meta.appendChild(createMetaLine(authorName));
    const secondLineParts = [];
    if (languageName)
        secondLineParts.push(languageName);
    if (secondLineParts.length > 0) {
        meta.appendChild(createMetaLine(secondLineParts.join(" • ")));
    }
    const badges = document.createElement("div");
    badges.className = "manga-badges";
    if (badges.childElementCount > 0)
        meta.appendChild(badges);
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
    if (tags)
        body.appendChild(tags);
    card.appendChild(cover);
    card.appendChild(body);
    return card;
}
// ==================== BUILDERS ДЛЯ ДЕТАЛЬНОЙ СТРАНИЦЫ (из manga.ts) ====================
function createLinkTag(type, text, id) {
    const tag = document.createElement("a");
    tag.href = `/${type}?query=${id}`;
    tag.textContent = text;
    tag.className = "tag__manga";
    return tag;
}
// Ключевые изменения: исправлены опечатки и тексты заголовков
function buildClickableTags(manga) {
    var _a;
    const tagsWrap = document.createElement("div");
    tagsWrap.id = "tags";
    tagsWrap.className = "tags";
    // Жанры
    if ((_a = manga.genres) === null || _a === void 0 ? void 0 : _a.length) {
        const genresBlock = document.createElement("div");
        genresBlock.id = "genres";
        const genresText = document.createElement("h2");
        genresText.textContent = "Жанры:";
        genresBlock.appendChild(genresText);
        manga.genres.forEach((genre) => {
            genresBlock.appendChild(createLinkTag("genre", genre.name, genre.id));
        });
        tagsWrap.appendChild(genresBlock);
    }
    // Автор
    if (manga.author) {
        const authorBlock = document.createElement("div");
        authorBlock.id = "author";
        const authorText = document.createElement("h2");
        authorText.textContent = "Автор:";
        authorBlock.appendChild(authorText);
        authorBlock.appendChild(createLinkTag("author", manga.author.name, manga.author.id));
        tagsWrap.appendChild(authorBlock);
    }
    // Язык
    if (manga.language) {
        const languageBlock = document.createElement("div");
        languageBlock.id = "language";
        const languageText = document.createElement("h2");
        languageText.textContent = "Язык:"; // ← исправлено
        languageBlock.appendChild(languageText);
        languageBlock.appendChild(createLinkTag("language", manga.language.name, manga.language.id));
        tagsWrap.appendChild(languageBlock);
    }
    return tagsWrap;
}
function buildInfo(manga) {
    const infoBlock = document.createElement("div");
    infoBlock.id = "info";
    const title = document.createElement("h1");
    title.textContent = manga.title;
    const poster = document.createElement("img");
    poster.src = manga.poster;
    poster.alt = `Обложка манги «${manga.title}»`;
    poster.loading = "lazy";
    poster.decoding = "async";
    poster.onerror = () => {
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
    infoBlock.append(poster, title);
    return infoBlock;
}
function buildMangaButtons(manga, botUrl) {
    const buttons = document.createElement("div");
    buttons.id = "button";
    buttons.className = "buttons";
    const skuButton = document.createElement("a");
    skuButton.textContent = "Скопировать артикул";
    skuButton.className = "button__sku";
    skuButton.id = "sku";
    skuButton.onclick = () => {
        navigator.clipboard
            .writeText(manga.sku)
            .then(() => {
            skuButton.textContent = "Скопировано!";
            setTimeout(() => {
                skuButton.textContent = "Скопировать артикул";
            }, 2000);
        })
            .catch((err) => {
            alert("Не удалось скопировать артикул: " + err);
        });
    };
    buttons.appendChild(skuButton);
    if (manga.gallery.length < 100 && botUrl) {
        const pdfButton = document.createElement("a");
        const botURL = new URL(botUrl);
        botURL.searchParams.append("start", manga.sku);
        pdfButton.textContent = "Скачать PDF";
        pdfButton.className = "button__pdf";
        pdfButton.id = "pdf";
        pdfButton.href = botURL.toString();
        buttons.appendChild(pdfButton);
    }
    if (manga.url) {
        const originalButton = document.createElement("a");
        originalButton.textContent = "Оригинал";
        originalButton.className = "button__manga";
        originalButton.id = "original";
        originalButton.href = manga.url;
        originalButton.target = "_blank";
        originalButton.rel = "noopener noreferrer";
        buttons.appendChild(originalButton);
    }
    return buttons;
}
function buildInfoBlockFull(manga, bot) {
    const wrapper = document.createElement("div");
    wrapper.id = "manga-info";
    wrapper.className = "manga-info";
    wrapper.append(buildInfo(manga), buildClickableTags(manga), buildMangaButtons(manga, bot), buildGallery(manga));
    return wrapper;
}
function buildImage(url, index) {
    const img = document.createElement("img");
    img.className = "gallery__image";
    img.src = url;
    img.id = `image-${index}`;
    img.loading = "lazy";
    img.alt = "Страница манги";
    return img;
}
function buildGallery(manga) {
    const gallery = document.createElement("div");
    gallery.id = "gallery";
    gallery.className = "gallery";
    for (let index = 0; index < manga.gallery.length; index++) {
        let url = manga.gallery[index];
        gallery.appendChild(buildImage(url, index));
    }
    return gallery;
}
function renderManga(manga, bot) {
    const container = document.getElementById("manga");
    if (!container)
        return;
    container.innerHTML = "";
    container.append(buildInfoBlockFull(manga, bot));
}
// ==================== API ====================
async function buildResponse(endpoint, page, query = null) {
    const baseUrl = API_ENDPOINTS[endpoint];
    const params = new URLSearchParams({
        page: String(page),
        per_page: String(ITEMS_PER_PAGE),
    });
    if (query && query.trim()) {
        params.set("query", query.trim());
    }
    const url = query
        ? `${baseUrl}?${params.toString()}`
        : `${API_ENDPOINTS["pages"]}?${params.toString()}`;
    const response = await fetch(url, {
        headers: { Accept: "application/json" },
    });
    if (!response.ok)
        throw new Error(`HTTP error: ${response.status}`);
    return (await response.json());
}
async function fetchManga(sku) {
    const response = await fetch(buildMangaURL(sku), {
        headers: { Accept: "application/json" },
    });
    if (!response.ok) {
        window.location.href = "/404";
    }
    return response.json();
}
async function fetchBot() {
    try {
        const response = await fetch(API_ENDPOINTS.bot, {
            headers: { Accept: "application/json" },
        });
        if (!response.ok)
            return null;
        const data = await response.json();
        return typeof data === "string" ? data : null;
    }
    catch (_a) {
        return null;
    }
}
// ==================== ФИЛЬТРАЦИЯ И ВЫБОР ТЕГА (ОБНОВЛЁННАЯ randomSelect) ====================
// Ключевые изменения:
// • Теперь возвращает структурированный объект (чистая архитектура, без мутации глобальных переменных)
// • Выбор только из существующих тегов манги (автор + жанры + язык)
// • Строгая фильтрация обеспечивается бэкендом (endpoint + query=id)
// • Исключены дубликаты и пустые кейсы
// • Оптимизировано — один проход по массивам
function getType(type) {
    if (type === "author")
        return "автора";
    if (type === "genre")
        return "жанра";
    return "языка";
}
function randomSelect(manga) {
    var _a;
    const tags = [];
    if (manga.author) {
        tags.push({ type: "author", object: manga.author });
    }
    if ((_a = manga.genres) === null || _a === void 0 ? void 0 : _a.length) {
        manga.genres.forEach(genre => {
            tags.push({ type: "genre", object: genre });
        });
    }
    if (manga.language) {
        tags.push({ type: "language", object: manga.language });
    }
    if (tags.length === 0) {
        return { endpoint: "pages", query: "", displayText: "Новинки" };
    }
    const randomIndex = Math.floor(Math.random() * tags.length);
    const selected = tags[randomIndex];
    return {
        endpoint: selected.type,
        query: selected.object.id.toString(),
        displayText: `Результаты по ${getType(selected.type)}: ${selected.object.name}`,
    };
}
// ==================== ГАЛЕРЕЯ И БЕСКОНЕЧНАЯ ЗАГРУЗКА (из index.ts) ====================
function setStateMessage(message) {
    if (!galleryEl)
        return;
    galleryEl.innerHTML = "";
    const state = document.createElement("div");
    state.className = "gallery-state";
    state.textContent = message;
    galleryEl.appendChild(state);
}
function renderMangas(items) {
    if (!galleryEl)
        return;
    const fragment = document.createDocumentFragment();
    items.forEach((item) => fragment.appendChild(buildManga(item)));
    galleryEl.appendChild(fragment);
}
function removeLoader() {
    if (loaderEl)
        loaderEl.remove();
}
async function loadMore(endpoint = null, query = null) {
    if (isLoading || !hasMore || !galleryEl)
        return;
    isLoading = true;
    if (loaderEl) {
        loaderEl.textContent = "Загрузка ещё...";
        loaderEl.style.display = "grid";
    }
    try {
        const result = await buildResponse(endpoint || activeEndpoint, currentPage, query || initialQuery);
        if (!result.success) {
            hasMore = false;
            if (currentPage === 1) {
                removeLoader();
                setStateMessage("Ничего не найдено.");
            }
            return;
        }
        if (totalItems === 0)
            totalItems = result.total;
        if (currentPage === 1)
            galleryEl.innerHTML = "";
        if (!result.response.length && currentPage === 1) {
            removeLoader();
            setStateMessage("Ничего не найдено.");
            hasMore = false;
            return;
        }
        renderMangas(result.response);
        const loadedCount = galleryEl.querySelectorAll(".manga").length;
        if (loadedCount >= totalItems || result.response.length < ITEMS_PER_PAGE) {
            hasMore = false;
            if (loaderEl)
                loaderEl.textContent = "Это всё";
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
        if (loaderEl)
            loaderEl.textContent = "Ошибка загрузки";
    }
    finally {
        isLoading = false;
    }
}
function initInfiniteScroll() {
    if (!loaderEl || observer)
        return;
    observer = new IntersectionObserver((entries) => {
        var _a;
        if ((_a = entries[0]) === null || _a === void 0 ? void 0 : _a.isIntersecting)
            void loadMore(randomTag.endpoint, randomTag.query);
    }, { root: null, rootMargin: "300px 0px", threshold: 0.01 });
    observer.observe(loaderEl);
}
// ==================== ОБЩИЕ ФУНКЦИИ (topbar + search) ====================
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
    topbar = document.querySelector(".topbar");
    if (!topbar)
        return;
    updateTopbarHeight();
    window.addEventListener("resize", () => { });
    window.addEventListener("scroll", handleScroll, { passive: true });
    lastScrollY = window.scrollY;
}
function initSearch() {
    if (!searchForm || !searchInput)
        return;
    searchInput.value = initialQuery;
    searchForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const value = searchInput.value.trim();
        if (value.length > 120) {
            // setError можно добавить при необходимости
            return;
        }
        const nextUrl = new URL(window.location.href);
        nextUrl.pathname = "/query";
        if (value)
            nextUrl.searchParams.set("query", value);
        else
            nextUrl.searchParams.delete("query");
        window.location.href = nextUrl.toString();
    });
}
// ==================== ЗАГРУЗКА ДЕТАЛЬНОЙ СТРАНИЦЫ + РЕКОМЕНДАЦИИ ====================
async function loadDetailAndRelated() {
    const sku = getSkuFromUrl();
    if (!sku) {
        window.location.href = "/";
        return;
    }
    const detailContainer = document.getElementById("manga");
    if (!detailContainer)
        return;
    try {
        const [mangaData, botUrl] = await Promise.all([fetchManga(sku), fetchBot()]);
        if (mangaData.author) {
            document.title = `${mangaData.author.name} | ${mangaData.title}`;
        }
        else if (mangaData.language) {
            document.title = `${mangaData.language.name} | ${mangaData.title}`;
        }
        else {
            document.title = mangaData.title;
        }
        // 1. Рендер полной информации о манге
        renderManga(mangaData, botUrl);
        // 2. Выбор случайного релевантного тега + строгая фильтрация
        randomTag = randomSelect(mangaData);
        // 3. Обновление заголовка рекомендаций
        if (textShowEl)
            textShowEl.textContent = randomTag.displayText;
        // 4. Подготовка галереи рекомендаций
        currentPage = 1;
        hasMore = true;
        totalItems = 0;
        if (galleryEl) {
            galleryEl.innerHTML = `<div class="gallery-state">Загрузка рекомендаций...</div>`;
        }
        initInfiniteScroll();
        // 5. Загрузка строго отфильтрованных результатов (бэкенд фильтрует по выбранному тегу)
        await loadMore(randomTag.endpoint, randomTag.query);
    }
    catch (err) {
        console.error(err);
        if (detailContainer) {
            detailContainer.innerHTML = `
        <div class="gallery-state">
          Не удалось загрузить мангу.<br>
          <a href="/" style="color:var(--accent);text-decoration:underline;">Вернуться на главную</a>
        </div>`;
        }
    }
}
// ==================== ГЛАВНАЯ СТРАНИЦА ====================
async function loadMainGallery() {
    if (!galleryEl)
        return;
    initInfiniteScroll();
    await loadMore(randomTag.endpoint, randomTag.query); // использует дефолтные activeEndpoint / initialQuery
}
// ==================== MAIN ====================
async function main() {
    initTopbarBehavior();
    initSearch();
    if (isDetailPage()) {
        await loadDetailAndRelated();
    }
    else {
        await loadMainGallery();
    }
}
void main();
