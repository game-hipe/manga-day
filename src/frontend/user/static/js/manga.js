"use strict";
// =============================================
// manga.ts — улучшенная версия для страницы manga.html
// =============================================
// ==================== ТИПЫ ====================
var activeEndpoint = "pages";
var initialQuery = '';
// ==================== УТИЛИТЫ ====================
function getSkuFromUrl() {
    const pathname = window.location.pathname.replace(/^\/+|\/+$/g, '');
    const parts = pathname.split('/');
    return parts[parts.length - 1] || null;
}
// ==================== СОЗДАНИЕ ЭЛЕМЕНТОВ ====================
function createLinkTag(type, text, id) {
    const tag = document.createElement('a');
    tag.href = `/${type}?query=${id}`;
    tag.textContent = text;
    tag.className = 'tag__manga';
    return tag;
}
function buildClickableTags(manga) {
    var _a;
    const tagsWrap = document.createElement('div');
    tagsWrap.id = 'tags';
    tagsWrap.className = 'tags';
    // Жанры
    if ((_a = manga.genres) === null || _a === void 0 ? void 0 : _a.length) {
        const genresBlock = document.createElement('div');
        const genresText = document.createElement('h2');
        genresText.textContent = 'Жанры:';
        genresBlock.appendChild(genresText);
        genresBlock.id = 'genres';
        manga.genres.forEach((genre) => {
            genresBlock.appendChild(createLinkTag('genre', genre.name, genre.id));
        });
        tagsWrap.appendChild(genresBlock);
    }
    // Автор
    if (manga.author) {
        const authorBlock = document.createElement('div');
        const AuthorText = document.createElement('h2');
        AuthorText.textContent = 'Автор:';
        authorBlock.appendChild(AuthorText);
        authorBlock.id = 'author';
        authorBlock.appendChild(createLinkTag('author', manga.author.name, manga.author.id));
        tagsWrap.appendChild(authorBlock);
    }
    // Язык
    if (manga.language) {
        const languageBlock = document.createElement('div');
        const langauageText = document.createElement('h2');
        langauageText.textContent = 'Автор:';
        languageBlock.appendChild(langauageText);
        languageBlock.id = 'language';
        languageBlock.appendChild(createLinkTag('language', manga.language.name, manga.language.id));
        tagsWrap.appendChild(languageBlock);
    }
    return tagsWrap;
}
function buildInfo(manga) {
    const infoBlock = document.createElement('div');
    infoBlock.id = 'info';
    const title = document.createElement('h1');
    title.textContent = manga.title;
    const poster = document.createElement('img');
    poster.src = manga.poster;
    poster.alt = `Обложка манги «${manga.title}»`;
    poster.loading = 'lazy';
    poster.decoding = 'async';
    // Fallback как в index.ts
    poster.onerror = () => {
        poster.src =
            'data:image/svg+xml;charset=UTF-8,' +
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
    infoBlock.append(title, poster);
    return infoBlock;
}
function buildMangaButtons(manga, botUrl) {
    const buttons = document.createElement('div');
    buttons.id = 'button';
    buttons.className = 'buttons';
    // PDF-кнопка
    if (manga.gallery.length < 100 && botUrl) {
        const pdfButton = document.createElement('a');
        const botURL = new URL(botUrl);
        botURL.searchParams.append('start', manga.sku); // ← исправлен баг (был глобальный sku)
        pdfButton.textContent = 'Скачать PDF';
        pdfButton.className = 'button__pdf';
        pdfButton.id = 'pdf';
        pdfButton.href = botURL.toString();
        buttons.appendChild(pdfButton);
    }
    // Кнопка оригинала
    if (manga.url) {
        const originalButton = document.createElement('a');
        originalButton.textContent = 'Оригинал';
        originalButton.className = 'button__manga';
        originalButton.id = 'original';
        originalButton.href = manga.url;
        originalButton.target = '_blank';
        originalButton.rel = 'noopener noreferrer';
        buttons.appendChild(originalButton);
    }
    return buttons;
}
function buildInfoBlockFull(manga, bot) {
    const wrapper = document.createElement('div');
    wrapper.id = 'manga-info';
    wrapper.className = 'manga-info';
    wrapper.append(buildInfo(manga), buildClickableTags(manga), buildMangaButtons(manga, bot));
    return wrapper;
}
function buildImage(url) {
    const img = document.createElement('img');
    img.className = 'gallery__image';
    img.src = url;
    img.loading = 'lazy';
    img.alt = 'Страница манги';
    return img;
}
function buildGallery(manga) {
    const gallery = document.createElement('div');
    gallery.id = 'gallery';
    gallery.className = 'gallery';
    manga.gallery.forEach((url) => {
        gallery.appendChild(buildImage(url));
    });
    return gallery;
}
function renderManga(manga, bot) {
    const container = document.getElementById('manga');
    if (!container)
        return;
    container.innerHTML = '';
    container.append(buildInfoBlockFull(manga, bot), buildGallery(manga));
}
// ==================== API ====================
async function fetchManga(sku) {
    const response = await fetch(buildMangaURL(sku), {
        headers: { Accept: 'application/json' },
    });
    if (!response.ok)
        throw new Error(`HTTP ${response.status}`);
    return response.json();
}
async function fetchBot() {
    try {
        const response = await fetch(API_ENDPOINTS.bot, {
            headers: { Accept: 'application/json' },
        });
        if (!response.ok)
            return null;
        const data = await response.json();
        return typeof data === 'string' ? data : null;
    }
    catch (_a) {
        return null;
    }
}
function getType(type) {
    if (type === "author") {
        return "автора";
    }
    else if (type === "genre") {
        return "жанра";
    }
    else {
        return "языка";
    }
}
function randomSelect(manga) {
    const Tags = [];
    if (manga.author) {
        Tags.push({
            type: "author",
            object: manga.author
        });
    }
    if (manga.genres) {
        manga.genres.forEach((genre) => {
            Tags.push({
                type: "genre",
                object: genre
            });
        });
    }
    if (manga.language) {
        Tags.push({
            type: 'language',
            object: manga.language
        });
    }
    if (Tags) {
        const index = Math.floor(Math.random() * Tags.length);
        const tag = Tags[index];
        activeEndpoint = tag.type;
        initialQuery = tag.object.id.toString();
        return `Результаты по поиску ${getType(tag.type)}: ${tag.object.name}`;
    }
    return `Новинки`;
}
// ==================== MAIN ====================
async function loadManga() {
    const sku = getSkuFromUrl();
    if (!sku) {
        window.location.href = '/';
        return;
    }
    const container = document.getElementById('manga');
    if (!container)
        return;
    try {
        const [mangaData, botUrl] = await Promise.all([
            fetchManga(sku),
            fetchBot(),
        ]);
        renderManga(mangaData, botUrl);
        var text = randomSelect(mangaData);
        var textShow = document.getElementById("textShow");
        if (textShow) {
            textShow.innerText = text;
        }
        document.title = `MangaDay | ${mangaData.title}`;
    }
    catch (err) {
        console.error(err);
        container.innerHTML = `
      <div class="gallery-state">
        Не удалось загрузить мангу.<br>
        <a href="/" style="color:var(--accent);text-decoration:underline;">Вернуться на главную</a>
      </div>`;
    }
}
// Запуск
loadManga();
