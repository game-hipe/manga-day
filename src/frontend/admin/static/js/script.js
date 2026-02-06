const ws = new WebSocket("ws://localhost:8000/admin/ws");
const stat_ws = new WebSocket("ws://localhost:8000/admin/ws/status")

// Массив для хранения текущих сообщений (для управления)
let activeMessages = [];

// Функции для управления модальным окном подтверждения
function ShowStopConfirmation() {
    const modal = document.getElementById("stopConfirmationModal");
    if (modal) {
        modal.style.display = "flex";
        // Блокируем прокрутку фона
        document.body.style.overflow = "hidden";
    }
}

function HideStopConfirmation() {
    const modal = document.getElementById("stopConfirmationModal");
    if (modal) {
        modal.style.display = "none";
        // Восстанавливаем прокрутку фона
        document.body.style.overflow = "auto";
    }
}

function ConfirmStopParsing() {
    HideStopConfirmation(); // Скрываем модальное окно
    
    // Отправляем команду остановки
    var command = "stop:all";
    ws.send(command);
    
    // Показываем уведомление об успешной отправке команды
    ShowMessage("Команда на остановку парсинга отправлена", "warning");
}

function UpdateStatus(message) {
    const statusDiv = document.getElementById("status");
    
    if (!statusDiv) {
        console.error("Элемент с id='status' не найден");
        return;
    }
    
    // Очищаем содержимое
    statusDiv.innerHTML = '';
    
    // Разделяем сообщение по строкам
    const lines = message.split('\n').filter(line => line.trim() !== '');
    
    if (lines.length === 0) {
        // Если нет строк, создаем пустое сообщение
        const emptyMessage = document.createElement("div");
        emptyMessage.textContent = "Нет активных процессов";
        emptyMessage.style.textAlign = "center";
        emptyMessage.style.padding = "20px";
        emptyMessage.style.opacity = "0.7";
        statusDiv.appendChild(emptyMessage);
        return;
    }
    
    // Создаем список
    const ul = document.createElement("ul");
    
    // Добавляем каждый статус
    lines.forEach((line, index) => {
        const li = document.createElement("li");
        const h1 = document.createElement("h1");
        
        // Устанавливаем содержимое с сохранением HTML тегов
        h1.innerHTML = line.trim();
        
        // Добавляем класс в зависимости от процента (опционально)
        if (line.includes("- 0%")) {
            li.style.borderLeftColor = "#ff416c"; // Красный для 0%
        } else if (line.includes("- 100%")) {
            li.style.borderLeftColor = "#00b09b"; // Зеленый для 100%
        }
        
        li.appendChild(h1);
        ul.appendChild(li);
    });
    
    statusDiv.appendChild(ul);
}

// Пример использования:
// UpdateStatus("Все системы работают нормально");

function ShowMessage(message, status) {
    const messagesContainer = document.querySelector('.messages');
    
    if (!messagesContainer) {
        console.error('Контейнер для сообщений не найден!');
        return;
    }
    
    // Проверяем допустимые статусы
    const validStatuses = ['info', 'warning', 'error', 'success'];
    if (!validStatuses.includes(status)) {
        console.warn(`Неизвестный статус: ${status}. Используется 'info' по умолчанию.`);
        status = 'info';
    }
    
    // Создаем новый элемент сообщения
    const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const messageElement = document.createElement('div');
    messageElement.id = messageId;
    messageElement.className = `message ${status}`;
    messageElement.innerHTML = `<h1><span>${message}</span></h1>`;
    
    // Добавляем сообщение в контейнер
    messagesContainer.appendChild(messageElement);
    
    // Добавляем в массив активных сообщений
    activeMessages.push({
        id: messageId,
        element: messageElement
    });
    
    // Удаляем сообщение через 4 секунды (0.5s анимация + 3.5s показа)
    setTimeout(() => {
        const msgIndex = activeMessages.findIndex(msg => msg.id === messageId);
        if (msgIndex !== -1) {
            // Удаляем элемент из DOM
            if (activeMessages[msgIndex].element && activeMessages[msgIndex].element.parentNode) {
                activeMessages[msgIndex].element.remove();
            }
            // Удаляем из массива
            activeMessages.splice(msgIndex, 1);
        }
    }, 4000);
}

function AcceptButton() {
    const button = document.getElementById("StartParsingButton");
    if (button) {
        button.disabled = false;
        button.style.opacity = "1";
        button.style.cursor = "pointer";
    }
}

function BlockButton() {
    UpdateStatus("Ожидаем статистику!")
    const button = document.getElementById("StartParsingButton");
    if (button) {
        button.disabled = true;
        button.style.opacity = "0.5";
        button.style.cursor = "not-allowed";
    }
}

function OnAlert(event) {
    var content = JSON.parse(event.data);
    var message = content.message;
    var level = content.level;

    if (message.startsWith("Парсинг завершен") || message.startsWith("Все парсеры завершили работу")) {
        AcceptButton();
    } else if (message.startsWith("Начало парсинга")) {
        BlockButton();
    }
    
    if (message.startsWith("Парсинг уже начат")) {
        BlockButton();
    }

    ShowMessage(message, level);
}

function OnStatus(event) {
    var content = event.data;
    if (content.includes("В работе")) {
    const button = document.getElementById("StartParsingButton");
        if (button) {
            button.disabled = true;
            button.style.opacity = "0.5";
            button.style.cursor = "not-allowed";
        }
    }
    UpdateStatus(content)
}

ws.onmessage = OnAlert;
stat_ws.onmessage = OnStatus


function StartParsing() {
    if (document.getElementById("StartParsingButton").disabled) {
        ShowMessage("Парсинг уже запущен", "warning");
        return;
    }

    var command = "start:all";
    ws.send(command);
}

// Старая функция StopParsing удалена, теперь используется ConfirmStopParsing

// Закрытие модального окна при клике на фон
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById("stopConfirmationModal");
    
    if (modal) {
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                HideStopConfirmation();
            }
        });
        
        // Закрытие по клавише Esc
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && modal.style.display === 'flex') {
                HideStopConfirmation();
            }
        });
    }
});

// Очистка всех сообщений при закрытии страницы
window.addEventListener('beforeunload', function() {
    activeMessages.forEach(msg => {
        if (msg.element && msg.element.parentNode) {
            msg.element.remove();
        }
    });
    activeMessages = [];
});