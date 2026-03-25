const URLJoin = (...args: string[]): string =>
  args
    .join("/")
    .replace(/[\/]+/g, "/")
    .replace(/^(.+):\//, "$1://")
    .replace(/^file:/, "file:/")
    .replace(/\/(\?|&|#[^!])/g, "$1")
    .replace(/\?/g, "&")
    .replace("&", "?");

const API = "http://localhost:8080/api/v1";

const API_ENDPOINTS = {
  author: URLJoin(API, "/pages/author"),
  language: URLJoin(API, "/pages/language"),
  genre: URLJoin(API, "/pages/genre"),
  query: URLJoin(API, "/pages/query"),
  pages: URLJoin(API, "/pages"),
} as const;

type EndpointKey = keyof typeof API_ENDPOINTS;

interface ObjectWithId {
  id: number;
  name: string;
}

interface Manga {
  id: number;
  title: string;
  poster: string;
  url: string;
  language: ObjectWithId | null;
  author: ObjectWithId | null;
  genres: ObjectWithId[];
  sku: string;
  rating?: number | null;
  status?: string | null;
}

interface ResponsePayload {
  query: string;
  success: boolean;
  total: number;
  page: number;
  page_now: number;
  response: Manga[];
}

const ITEMS_PER_PAGE = 10;
const TAG_LIMIT = 6;
const DEFAULT_ENDPOINT: EndpointKey = "query";

function getActiveEndpoint(): EndpointKey {
  const pathname = window.location.pathname.replace(/^\/+|\/+$/g, "");
  if (pathname in API_ENDPOINTS) {
    return pathname as EndpointKey;
  }
  return DEFAULT_ENDPOINT;
}

function createTextBadge(text: string, className: string): HTMLSpanElement {
  const badge = document.createElement("span");
  badge.className = className;
  badge.textContent = text;
  return badge;
}

function createMetaLine(text: string): HTMLDivElement {
  const line = document.createElement("div");
  line.className = "manga-meta-line";
  line.textContent = text;
  return line;
}

function formatRating(value: number | null | undefined): string | null {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return null;
  }
  const rounded = Math.round(value * 10) / 10;
  return `★ ${rounded.toFixed(1)}`;
}

function buildTags(genres: ObjectWithId[]): HTMLDivElement | null {
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

function buildInfoBlock(manga: Manga): HTMLDivElement {
  const meta = document.createElement("div");
  meta.className = "manga-meta";

  const authorName = manga.author?.name ?? null;
  const languageName = manga.language?.name ?? null;
  const ratingText = formatRating(manga.rating);
  const statusText = manga.status?.trim() || null;

  if (authorName) {
    meta.appendChild(createMetaLine(authorName));
  }

  const secondLineParts: string[] = [];
  if (languageName) secondLineParts.push(languageName);
  if (statusText) secondLineParts.push(statusText);

  if (secondLineParts.length > 0) {
    meta.appendChild(createMetaLine(secondLineParts.join(" • ")));
  }

  const badges = document.createElement("div");
  badges.className = "manga-badges";

  if (ratingText) {
    badges.appendChild(createTextBadge(ratingText, "badge badge--rating"));
  }

  if (statusText) {
    badges.appendChild(createTextBadge(statusText, "badge badge--status"));
  }

  if (badges.childElementCount > 0) {
    meta.appendChild(badges);
  }

  return meta;
}

function buildManga(manga: Manga): HTMLAnchorElement {
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

async function buildResponse(
  endpoint: EndpointKey,
  page: number,
  query: string | null = null
): Promise<ResponsePayload> {
  const baseUrl = API_ENDPOINTS[endpoint];
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(ITEMS_PER_PAGE),
  });

  if (query && query.trim()) {
    params.set("query", query.trim());
  }
  var response: Response;

  if (query) {
    response = await fetch(`${baseUrl}/?${params.toString()}`, {
        headers: {
        Accept: "application/json",
        },
    });
  } else {
    response = await fetch(`${API_ENDPOINTS['pages']}/?${params.toString()}`, {
        headers: {
        Accept: "application/json",
        },
    });
  }

  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  return (await response.json()) as ResponsePayload;
}

const gallery = document.getElementById("gallery") as HTMLElement | null;
const loader = document.getElementById("loader") as HTMLElement | null;
const searchForm = document.getElementById("search-form") as HTMLFormElement | null;
const searchInput = document.getElementById("search-input") as HTMLInputElement | null;
const searchError = document.getElementById("search-error") as HTMLElement | null;

const activeEndpoint = getActiveEndpoint();
const currentUrl = new URL(window.location.href);
const initialQuery = currentUrl.searchParams.get("query") ?? "";

let currentPage = 1;
let isLoading = false;
let hasMore = true;
let totalItems = 0;
let observer: IntersectionObserver | null = null;

function setStateMessage(message: string): void {
  if (!gallery) return;
  gallery.innerHTML = "";
  const state = document.createElement("div");
  state.className = "gallery-state";
  state.textContent = message;
  gallery.appendChild(state);
}

function setError(message: string): void {
  if (!searchError) return;
  searchError.textContent = message;
}

function clearError(): void {
  setError("");
}

function renderMangas(items: Manga[]): void {
  if (!gallery) return;

  const fragment = document.createDocumentFragment();
  items.forEach((item) => fragment.appendChild(buildManga(item)));
  gallery.appendChild(fragment);
}

async function loadMore(): Promise<void> {
  if (isLoading || !hasMore || !gallery) return;

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
    } else {
      currentPage += 1;
    }
  } catch (error) {
    console.error("Ошибка при загрузке:", error);
    if (currentPage === 1) {
      setStateMessage("Не удалось загрузить мангу. Попробуйте ещё раз.");
    }
    hasMore = false;
    if (loader) {
      loader.textContent = "Ошибка загрузки";
    }
  } finally {
    isLoading = false;
  }
}

function initInfiniteScroll(): void {
  if (!loader) return;

  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting) {
        void loadMore();
      }
    },
    {
      root: null,
      rootMargin: "300px 0px",
      threshold: 0.01,
    }
  );

  observer.observe(loader);
}

function initSearch(): void {
  if (!searchForm || !searchInput) return;

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
    

    if (value) {
      nextUrl.searchParams.set("query", value);
    } else {
      nextUrl.searchParams.delete("query");
    }

    window.location.href = nextUrl.toString();
  });
}

async function main(): Promise<void> {
  if (!gallery) return;

  initSearch();
  initInfiniteScroll();

  if (!initialQuery) {
    // Ничего специального не делаем — просто загружаем первую страницу.
  }

  await loadMore();
}

void main();