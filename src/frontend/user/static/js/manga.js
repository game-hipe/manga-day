"use strict";
const parts = document.location.href.split("/");
const sku = parts[parts.length - 1];
if (sku === undefined) {
    alert("Не удалось загрузить мангу...");
    document.location.href = "/";
}
function createTag(type, text, id) {
    var tag = document.createElement("a");
    var href = `/${type}?query=${id}`;
    tag.href = href,
        tag.innerText = text,
        tag.className = "tag__manga";
    return tag;
}
function buildClickableTags(manga) {
    const tagsWrap = document.createElement("div");
    tagsWrap.id = "tags";
    tagsWrap.className = "tags";
    if (manga.genres.length != 0) {
        var tagsBlock = document.createElement("div");
        tagsBlock.id = "genres";
        manga.genres.forEach((genre) => {
            tagsBlock.appendChild(createTag("genre", genre.name, genre.id));
        });
        tagsWrap.append(tagsBlock);
    }
    if (manga.author) {
        var authorBlock = document.createElement("div");
        authorBlock.id = "author",
            authorBlock.appendChild(createTag("author", manga.author.name, manga.author.id));
        tagsWrap.append(authorBlock);
    }
    if (manga.language) {
        var languageBlock = document.createElement("div");
        languageBlock.id = "language";
        languageBlock.appendChild(createTag("language", manga.language.name, manga.language.id));
        tagsWrap.append(languageBlock);
    }
    return tagsWrap;
}
function buildInfo(manga) {
    const infoBlock = document.createElement("div");
    infoBlock.id = "info";
    const title = document.createElement("h1");
    title.innerText = manga.title;
    const poster = document.createElement("img");
    poster.src = manga.poster,
        infoBlock.append(title, poster);
    return infoBlock;
}
function buildMangaButtons(manga, botUrl) {
    const buttons = document.createElement("div");
    buttons.id = "button";
    buttons.className = "buttons";
    if (manga.gallery.length < 100 && botUrl) {
        var pdfButton = document.createElement("a");
        var botURL = new URL(botUrl);
        botURL.searchParams.append("start", sku);
        pdfButton.innerText = "Скачать PDF";
        pdfButton.className = "button__pdf";
        pdfButton.id = "pdf";
        pdfButton.href = botURL.toString();
        buttons.append(pdfButton);
    }
    if (manga.url) {
        const originalButton = document.createElement("a");
        originalButton.innerText = "Оригинал";
        originalButton.className = "button__manga";
        originalButton.id = "original";
        originalButton.href = manga.url;
        buttons.append(originalButton);
    }
    return buttons;
}
function buildInfoBlockFull(manga, bot) {
    const mangaDiv = document.createElement("div");
    mangaDiv.id = "manga-info";
    mangaDiv.className = "manga-info";
    const infoBlock = buildInfo(manga);
    const tagsWrap = buildClickableTags(manga);
    const buttons = buildMangaButtons(manga, bot);
    mangaDiv.append(infoBlock, tagsWrap, buttons);
    return mangaDiv;
}
function buildImage(url) {
    const image = document.createElement("img");
    image.className = "gallery__image";
    image.src = url;
    image.loading = "lazy";
    return image;
}
function buildGallery(manga) {
    const gallery = document.createElement("div");
    gallery.id = "gallery";
    gallery.className = "gallery";
    manga.gallery.forEach((url) => {
        gallery.append(buildImage(url));
    });
    return gallery;
}
function buildFullManga(manga, bot) {
    const mangaDiv = document.getElementById("manga");
    if (!mangaDiv) {
        alert("Не удалось загрузить мангу...");
        document.location.href = "/";
        return;
    }
    else {
        mangaDiv.innerText = ``;
    }
    const infoBlock = buildInfoBlockFull(manga, bot);
    const gallery = buildGallery(manga);
    mangaDiv.append(infoBlock, gallery);
}
async function fetchManga() {
    if (!sku) {
        alert("Не удалось загрузить мангу...");
        document.location.href = "/";
        return;
    }
    const response = await fetch(buildMangaURL(sku), {
        headers: {
            Accept: "application/json",
        },
    });
    if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }
    return (await response.json());
}
async function fetchBot() {
    const response = await fetch(API_ENDPOINTS['bot'], {
        headers: {
            Accept: "application/json",
        },
    });
    if (!response.ok) {
        return null;
    }
    return (await response.json());
}
async function loadManga() {
    var manga = await fetchManga();
    var bot = await fetchBot();
    if (!manga) {
        alert("Не удалось загрузить мангу...");
        document.location.href = "/";
        return;
    }
    buildFullManga(manga, bot);
}
loadManga();
