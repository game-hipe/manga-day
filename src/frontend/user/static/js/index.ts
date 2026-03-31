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
}

interface ResponsePayload {
    query: string;
    success: boolean;
    total: number;
    page: number;
    page_now: number;
    response: Manga[];
}

const ITEMS_PER_PAGE = 24;
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

  if (authorName) {
    meta.appendChild(createMetaLine(authorName));
  }

  const secondLineParts: string[] = [];
  if (languageName) secondLineParts.push(languageName);

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
    response = await fetch(`${baseUrl}?${params.toString()}`, {
        headers: {
        Accept: "application/json",
        },
    });
  } else {
    response = await fetch(`${API_ENDPOINTS['pages']}?${params.toString()}`, {
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

const currentUrl = new URL(window.location.href);
var activeEndpoint = getActiveEndpoint();
var initialQuery = currentUrl.searchParams.get("query") ?? "";

let currentPage = (() => {
  const p = parseInt(currentUrl.searchParams.get("page") ?? "", 10);
  return isNaN(p) || p < 1 ? 1 : p;
})();
let isLoading = false;
let hasMore = true;
let totalItems = 0;
let observer: IntersectionObserver | null = null;
let itemsLoaded = 0;      // кумулятивное количество загруженных элементов (учитывает пропущенные страницы)
let isFirstLoad = true;   // флаг первой загрузки (заменяет currentPage === 1)

if (currentPage > 1) {
  itemsLoaded = (currentPage - 1) * ITEMS_PER_PAGE;
}

// --- Topbar hide/show on scroll ---
let topbar: HTMLElement | null = null;
let topbarHeight = 0;
let isTopbarHidden = false;
let lastScrollY = 0;
let scrollTimeout: number | null = null;

function updateTopbarHeight() {
  if (!topbar) return;
  const newHeight = topbar.offsetHeight;
  if (newHeight > 0 && !isTopbarHidden) {
    topbarHeight = newHeight;
    document.documentElement.style.setProperty('--topbar-height', `${topbarHeight}px`);
  } else if (isTopbarHidden) {
    // if hidden, keep variable zero but remember actual height for later
    const actualHeight = topbar.offsetHeight;
    if (actualHeight > 0) topbarHeight = actualHeight;
  }
}

function showTopbar() {
  if (!topbar || !isTopbarHidden) return;
  topbar.classList.remove('topbar--hidden');
  isTopbarHidden = false;
  document.documentElement.style.setProperty('--topbar-height', `${topbarHeight}px`);
}

function hideTopbar() {
  if (!topbar || isTopbarHidden) return;
  topbar.classList.add('topbar--hidden');
  isTopbarHidden = true;
  document.documentElement.style.setProperty('--topbar-height', '0px');
}

function handleScroll() {
  if (scrollTimeout) return;
  scrollTimeout = window.requestAnimationFrame(() => {
    const currentScrollY = window.scrollY;
    // only act if scrolled enough (avoid hiding when barely moved)
    const scrollDelta = currentScrollY - lastScrollY;
    if (scrollDelta > 8 && currentScrollY > topbarHeight) {
      // scrolling down
      hideTopbar();
    } else if (scrollDelta < -8) {
      // scrolling up
      showTopbar();
    }
    lastScrollY = currentScrollY;
    scrollTimeout = null;
  });
}

function initTopbarBehavior() {
  topbar = document.querySelector('.topbar');
  if (!topbar) return;

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

async function tryLoadManga() {
  const baseUrl = API_ENDPOINTS["manga"];
  const response = await fetch(`${baseUrl}${initialQuery}`, {
      headers: {
      Accept: "application/json",
      },
  });

  if (response.ok) {
    window.location.href = `/manga/${initialQuery}`;
  }
}

function removeLoader(): void {
    if (loader) {
        loader.remove();
    }
}

async function loadMore(endpoint: EndpointKey | null = null, query: string | null = null): Promise<void> {
  if (isLoading || !hasMore || !gallery) return;

  isLoading = true;
  if (loader) {
    loader.textContent = "Загрузка ещё...";
    loader.style.display = "grid";
  }

  try {
    const result = await buildResponse(endpoint || activeEndpoint, currentPage, query || initialQuery);

    if (!isFirstLoad) {
      const url = new URL(window.location.href);
      url.searchParams.set('page', currentPage.toString());
      window.history.pushState({}, '', url);
    }

    if (initialQuery && result.total == 0) {
      await tryLoadManga();
    }
    if (!result.success) {
      hasMore = false;
      if (isFirstLoad) {                    // ← обобщили
        removeLoader();
        setStateMessage("Ничего не найдено.");
      }
      return;
    }

    if (totalItems === 0) {
      totalItems = result.total;
    }

    // === ИСПРАВЛЕНИЕ: очищаем плейсхолдер ВСЕГДА при первой загрузке ===
    if (isFirstLoad) {
      gallery.innerHTML = "";
      isFirstLoad = false;
    }

    // === ИСПРАВЛЕНИЕ: проверка «ничего не найдено» теперь по isFirstLoad ===
    if (!result.response.length && isFirstLoad) {
      removeLoader();
      setStateMessage("Ничего не найдено.");
      hasMore = false;
      return;
    }

    renderMangas(result.response);

    // === ИСПРАВЛЕНИЕ: кумулятивный счётчик (учитывает пропущенные страницы) ===
    itemsLoaded += result.response.length;

    if (itemsLoaded >= totalItems || result.response.length < ITEMS_PER_PAGE) {
      hasMore = false;
      if (loader) {
        loader.textContent = "Это всё";
      }
    } else {
      currentPage += 1;
    }
  } catch (error) {
    console.error("Ошибка при загрузке:", error);
    if (isFirstLoad) {                      // ← обобщили
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
    nextUrl.pathname = "/query"

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

  initTopbarBehavior();
  initSearch();
  initInfiniteScroll();

  await loadMore();
}

void main();