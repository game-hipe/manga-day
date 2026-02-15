var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var websocket = new WebSocket("ws://".concat(window.location.host, "/admin/ws"));
var spiderStatus;
var alertLevel;
var activeMessages = [];
function StartAllSpider() {
    return __awaiter(this, void 0, void 0, function () {
        var error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, fetch("/admin/command", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                signal: "start",
                                spider: "all"
                            })
                        })];
                case 1:
                    _a.sent();
                    return [3 /*break*/, 3];
                case 2:
                    error_1 = _a.sent();
                    console.error("Ошибка при отправке команды:", error_1);
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    });
}
function StopAllSpider() {
    return __awaiter(this, void 0, void 0, function () {
        var error_2;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, fetch("/admin/command", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                signal: "stop",
                                spider: "all"
                            })
                        })];
                case 1:
                    _a.sent();
                    return [3 /*break*/, 3];
                case 2:
                    error_2 = _a.sent();
                    console.error("Ошибка при отправке команды:", error_2);
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    });
}
function StartSpider(spiderName, page) {
    return __awaiter(this, void 0, void 0, function () {
        var error_3;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, fetch("/admin/command", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                signal: "start",
                                spider: spiderName,
                                page: page
                            })
                        })];
                case 1:
                    _a.sent();
                    return [3 /*break*/, 3];
                case 2:
                    error_3 = _a.sent();
                    console.error("Ошибка при отправке команды:", error_3);
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    });
}
function StopSpider(spiderName) {
    return __awaiter(this, void 0, void 0, function () {
        var error_4;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, fetch("/admin/command", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                signal: "stop",
                                spider: spiderName
                            })
                        })];
                case 1:
                    _a.sent();
                    return [3 /*break*/, 3];
                case 2:
                    error_4 = _a.sent();
                    console.error("Ошибка при отправке команды:", error_4);
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    });
}
function UpdateSpider(spider) {
    var _a;
    var spiderFound = false;
    var spiderBox = document.getElementById("Spiders");
    if (!spiderBox) {
        console.warn("Элемент 'Spiders' не найден.");
        return;
    }
    // Удаляем заглушку <strong>, если она есть
    var strong = spiderBox.querySelector("strong");
    strong === null || strong === void 0 ? void 0 : strong.remove();
    var spiderName = spider.name;
    var spiderStatus = spider.status;
    var spiderMessage = spider.message;
    var spiderChilds = spiderBox.querySelectorAll('.spider');
    // Поиск существующей карточки паука
    for (var index = 0; index < spiderChilds.length; index++) {
        var element = spiderChilds[index];
        var h1 = element.querySelector("h1");
        var p = element.querySelector("p");
        var b = element.querySelector("b");
        if (h1 && h1.innerText === spiderName) {
            spiderFound = true;
            // Создаём новую карточку взамен старой (чтобы не копить обработчики)
            if (p && p.innerText != spiderStatus || b && b.innerText != spiderMessage) {
                var newDiv = document.createElement("div");
                newDiv.className = "spider";
                // Заголовок с именем паука
                var newH1 = document.createElement("h1");
                newH1.textContent = spiderName;
                newDiv.appendChild(newH1);
                // Статус
                var newP = document.createElement("p");
                newP.textContent = spiderStatus;
                newDiv.appendChild(newP);
                newP.style.color = getColor(spiderStatus);
                // Сообщение
                var newB = document.createElement("b");
                newB.textContent = spiderMessage;
                newDiv.appendChild(newB);
                // Поле для номера страницы (может быть полезно)
                var pageInput = document.createElement("input");
                pageInput.setAttribute("type", "number");
                newDiv.appendChild(pageInput);
                // Кнопка с data-атрибутом (без обработчика)
                var newButton = document.createElement("button");
                newButton.textContent = spiderStatus === "not_running" ? "Начать парсинг" : "Остановить парсинг";
                newButton.dataset.spider = spiderName;
                newDiv.appendChild(newButton);
                // Заменяем старую карточку новой
                (_a = element.parentNode) === null || _a === void 0 ? void 0 : _a.replaceChild(newDiv, element);
                break;
            }
        }
    }
    // Если паук не найден, создаём новую карточку
    if (!spiderFound) {
        var divSpider = document.createElement("div");
        divSpider.className = "spider";
        var h1 = document.createElement("h1");
        h1.textContent = spiderName;
        divSpider.appendChild(h1);
        var p = document.createElement("p");
        p.style.color = getColor(spiderStatus);
        p.textContent = spiderStatus;
        divSpider.appendChild(p);
        var b = document.createElement("b");
        b.textContent = spiderMessage;
        divSpider.appendChild(b);
        var page = document.createElement("input");
        page.setAttribute("type", "number");
        divSpider.appendChild(page);
        var button = document.createElement("button");
        button.textContent = spiderStatus === "not_running" ? "Начать парсинг" : "Остановить парсинг";
        button.dataset.spider = spiderName; // сохраняем имя паука
        divSpider.appendChild(button);
        spiderBox.appendChild(divSpider);
    }
}
function getColor(status) {
    switch (status) {
        case "error":
            return "#F44336"; // Яркий красный - опасность, ошибка
        case "cancelled":
            return "#FF9800"; // Оранжевый - отмена, предупреждение
        case "not_running":
            return "#9E9E9E"; // Серый - неактивно, ожидание
        case "success":
            return "#4CAF50"; // Зеленый - успех, готово
        case "running":
            return "#2196F3"; // Синий - в процессе, активно
        case "processing":
            return "#FFC107"; // Янтарный - обработка, внимание
        default:
            return "";
    }
}
function OnAlert(message, level) {
    var messagesContainer = document.querySelector('.messages');
    if (!messagesContainer) {
        console.error('Контейнер для сообщений не найден!');
        return;
    }
    var messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    var messageElement = document.createElement('div');
    messageElement.id = messageId;
    messageElement.className = "message ".concat(level);
    messageElement.innerHTML = "<h1><span>".concat(message, "</span></h1>");
    messagesContainer.appendChild(messageElement);
    activeMessages.push({
        id: messageId,
        element: messageElement
    });
    setTimeout(function () {
        var msgIndex = activeMessages.findIndex(function (msg) { return msg.id === messageId; });
        if (msgIndex !== -1) {
            if (activeMessages[msgIndex].element && activeMessages[msgIndex].element.parentNode) {
                activeMessages[msgIndex].element.remove();
            }
            activeMessages.splice(msgIndex, 1);
        }
    }, 4000);
}
// --- Обработчик кликов через делегирование ---
document.addEventListener("DOMContentLoaded", function () {
    var spiderBox = document.getElementById("Spiders");
    if (spiderBox) {
        spiderBox.addEventListener("click", function (event) {
            var _a;
            var target = event.target;
            var button = target.closest("button");
            if (!button)
                return; // клик не по кнопке
            var spiderDiv = button.closest(".spider");
            if (!spiderDiv)
                return; // кнопка не внутри карточки паука
            var spiderName = button.dataset.spider;
            var spiderInput = spiderDiv.querySelector("input");
            var intPage = null;
            var stringPage = spiderInput === null || spiderInput === void 0 ? void 0 : spiderInput.value;
            if (stringPage) {
                intPage = parseInt(stringPage);
            }
            if (!spiderName)
                return; // нет data-атрибута
            // Определяем действие по тексту кнопки
            if ((_a = button.textContent) === null || _a === void 0 ? void 0 : _a.includes("Начать")) {
                StartSpider(spiderName, intPage);
            }
            else {
                StopSpider(spiderName);
            }
        });
    }
});
websocket.onmessage = function (event) {
    var answer = JSON.parse(event.data);
    console.log(answer);
    if (answer.signal === "alert") {
        var result = answer.result;
        OnAlert(result.message, result.level);
    }
    else if (answer.signal === "status") {
        var result = answer.result;
        for (var _i = 0, result_1 = result; _i < result_1.length; _i++) {
            var element = result_1[_i];
            UpdateSpider(element);
        }
    }
};
