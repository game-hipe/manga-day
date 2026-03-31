"use strict";
const URLJoin = (...args) => args
    .join("/")
    .replace(/[\/]+/g, "/")
    .replace(/^(.+):\//, "$1://")
    .replace(/^file:/, "file:/")
    .replace(/\/(\?|&|#[^!])/g, "$1")
    .replace(/\?/g, "&")
    .replace("&", "?");
const API_ORIGIN = window.__API__;
const API_PATH = "/api/v1";
const API = API_ORIGIN.use_type === "api_url"
    ? URLJoin(API_ORIGIN.value, API_PATH)
    : (() => {
        const url = new URL(document.location.href);
        url.port = API_ORIGIN.value;
        return URLJoin(url.toString(), API_PATH);
    })();
const API_ENDPOINTS = {
    author: URLJoin(API, "/pages/author"),
    language: URLJoin(API, "/pages/language"),
    genre: URLJoin(API, "/pages/genre"),
    query: URLJoin(API, "/pages/query"),
    pages: URLJoin(API, "/pages"),
    manga: URLJoin(API, "/manga/sku/"),
    bot: URLJoin(API, "/bot"),
};
function buildMangaURL(sku) {
    return URLJoin(API_ENDPOINTS['manga'], sku);
}
