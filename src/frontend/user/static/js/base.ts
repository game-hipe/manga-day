const URLJoin = (...args: string[]): string =>
  args
    .join("/")
    .replace(/[\/]+/g, "/")
    .replace(/^(.+):\//, "$1://")
    .replace(/^file:/, "file:/")
    .replace(/\/(\?|&|#[^!])/g, "$1")
    .replace(/\?/g, "&")
    .replace("&", "?");

const API_ORIGIN = new URL(window.location.origin);
API_ORIGIN.port = window?.__API_PORT__ || "8080"

const API = URLJoin(API_ORIGIN.toString(), "/api/v1");

const API_ENDPOINTS = {
  author: URLJoin(API, "/pages/author"),
  language: URLJoin(API, "/pages/language"),
  genre: URLJoin(API, "/pages/genre"),
  query: URLJoin(API, "/pages/query"),
  pages: URLJoin(API, "/pages"),
  manga: URLJoin(API, "/manga/sku/"),
  bot: URLJoin(API, "/bot"),
} as const;

type EndpointKey = keyof typeof API_ENDPOINTS;

function buildMangaURL(sku: string): string {
    return URLJoin(API_ENDPOINTS['manga'], sku);
}