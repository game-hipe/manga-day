const URLJoin = (...args: string[]) =>
  args
    .join("/")
    .replace(/[\/]+/g, "/")
    .replace(/^(.+):\//, "$1://")
    .replace(/^file:/, "file:/")
    .replace(/\/(\?|&|#[^!])/g, "$1")
    .replace(/\?/g, "&")
    .replace("&", "?");

const API = "http://localhost:8080/api/v1"
const API_ENDPOINTS = {
    author: URLJoin(API, "/pages/author"),
    language: URLJoin(API, "/pages/language"),
    genre: URLJoin(API, "/pages/genre")
} as const
type EndpointKey = keyof typeof API_ENDPOINTS


interface ObjectWithId {
    id: number
    name: string
}

interface Manga {
    id: number
    title: string
    poster: string
    url: string // Ссылка на оригинальную мангу не путать с ссылкой на страницу!
    language: ObjectWithId | null
    author: ObjectWithId | null
    genres: ObjectWithId[]
    sku: string
}

interface Response {
    query: string
    success: boolean
    total: number
    page: number
    page_now: number
    response: Manga[]
}

const nameMap = {
    'language': 'Язык',
    'author': 'Автор',
    'genre': 'Жанры'
} as const;

type NameMapKey = keyof typeof nameMap;

function buildDiv(objects: (ObjectWithId | null)[], name: string): HTMLDivElement | null {
    /**
     * Построить div с объектами
     */
    if (!objects) {
        return null
    } else if (objects[0] === null) {
        return null
    } else if (objects.length === 0) {
        return null
    }

    const objDiv = document.createElement('div')

    var metaBox = document.createElement('div')
    var tagBox = document.createElement('div')

    metaBox.className = 'tag-title__meta'
    metaBox.innerText = nameMap[name as NameMapKey] + ': '

    tagBox.className = 'tag-tags__meta'

    for (let index = 0; index < objects.length; index++) {
        if (index == 15) {
            break
        }
        const element = objects[index];
        if (!element) {
            continue
        }

        let tag = document.createElement('a')

        tag.innerText = element.name
        tag.className = 'tag'
        tag.href = `/${name}?query=${element.id}`

        tagBox.appendChild(tag)
    }

    objDiv.appendChild(metaBox)
    objDiv.appendChild(tagBox)

    return objDiv
}

function buildManga(manga: Manga): HTMLDivElement {
    const mangaDiv = document.createElement('div')
    mangaDiv.className = 'manga'

    var language: HTMLDivElement | null = buildDiv([manga.language], "language")
    var author: HTMLDivElement | null = buildDiv([manga.author], "author")
    var genres: HTMLDivElement | null = buildDiv(manga.genres, "genre")

    var title = document.createElement('h2')

    var redirect = document.createElement('a')
    var poster = document.createElement('img')

    title.innerText = manga.title
    poster.src = manga.poster
    poster.loading = "lazy"
    redirect.href = `/manga/${manga.sku}`

    redirect.appendChild(poster)

    mangaDiv.appendChild(redirect)
    mangaDiv.appendChild(title)

    if (language) {
        mangaDiv.appendChild(language)
    }

    if (author) {
        mangaDiv.appendChild(author)
    }

    if (genres) {
        mangaDiv.appendChild(genres)
    }

    return mangaDiv
}

async function buildResponse(endpoint: EndpointKey, page: number, query: string | null = null): Promise<Response> {
    var url = API_ENDPOINTS[endpoint];
    if (!url) {
        url = URLJoin(API, "/pages")
    }
    console.log(url);
    
    let params: URLSearchParams;

    if (query) {
        params = new URLSearchParams({
            query: query,
            page: page.toString(),
            per_page: '24'
        });
    } else {
        params = new URLSearchParams({
            page: page.toString(),
            per_page: '24'
        });
    }
    
    const fullUrl = `${url}/?${params.toString()}`;
    
    const response = await fetch(fullUrl);
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json() as Response;
}

// === НОВАЯ ЛОГИКА БЕСКОНЕЧНОГО СКРОЛЛИНГА (используем buildResponse как есть) ===
const mangaType = window.location.pathname.replace("/", "") as EndpointKey
const url = new URL(window.location.href)
const query: string | null = url.searchParams.get("query") // убрал лишний cast, чтобы явно было null

let currentPage = 1
let isLoading = false
let hasMore = true
let totalItems = 0
const PER_PAGE = 1 // оставили как в оригинальном buildResponse

async function loadMore() {
    if (isLoading || !hasMore) return

    isLoading = true

    try {
        const result = await buildResponse(mangaType, currentPage, query)

        if (!result.success) {
            console.log("Бля")
            return
        }

        // Запоминаем общее количество только один раз (из первого ответа)
        if (totalItems === 0) {
            totalItems = result.total
        }

        const gallery = document.getElementById("gallery")
        if (!gallery) {
            return
        }

        for (let index = 0; index < result.response.length; index++) {
            const element = result.response[index]
            gallery.appendChild(buildManga(element))
        }

        // Проверяем, есть ли ещё данные
        if (currentPage * PER_PAGE >= totalItems) {
            hasMore = false
        } else {
            currentPage++
        }
    } catch (error) {
        console.error("Ошибка при загрузке:", error)
    } finally {
        isLoading = false
    }
}

async function main() {
    const gallery = document.getElementById("gallery")
    if (!gallery) {
        return
    }

    // Удаляем старый h1 (как в оригинале)
    var h1 = gallery.querySelector("h1")
    if (h1) {
        h1.remove()
    }

    // Первая загрузка (всегда с 1 страницы — классика infinite scroll)
    await loadMore()

    // Обработчик бесконечного скролла
    window.addEventListener("scroll", () => {
        if (isLoading || !hasMore) return

        const scrollTop = window.scrollY
        const clientHeight = window.innerHeight
        const scrollHeight = document.documentElement.scrollHeight

        // Подгружаем за 300px до конца (можно менять)
        if (scrollTop + clientHeight >= scrollHeight - 300) {
            loadMore()
        }
    })
}

main()