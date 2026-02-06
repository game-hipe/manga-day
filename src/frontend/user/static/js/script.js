document.addEventListener('DOMContentLoaded', function() {
    const skuButtons = document.querySelectorAll('.sku-btn');
    const notification = document.getElementById('copyNotification');
    
    skuButtons.forEach(button => {
        button.addEventListener('click', function() {
            const skuCode = this.getAttribute('data-sku');
            
            // Используем современный Clipboard API
            navigator.clipboard.writeText(skuCode)
                .then(() => {
                    // Показываем уведомление
                    notification.classList.add('show');
                    
                    // Скрываем уведомление через 2 секунды
                    setTimeout(() => {
                        notification.classList.remove('show');
                    }, 2000);
                    
                    // Визуальная обратная связь на кнопке
                    this.style.backgroundColor = '#4CAF50';
                    this.style.color = 'white';
                    this.textContent = 'Скопировано!';
                    
                    setTimeout(() => {
                        this.style.backgroundColor = '';
                        this.style.color = '';
                        this.textContent = 'Сюда';
                    }, 2000);
                })
                .catch(err => {
                    console.error('Ошибка при копировании: ', err);
                    // Fallback для старых браузеров
                    fallbackCopy(skuCode);
                });
        });
    });
    
    // Резервный метод для старых браузеров
    function fallbackCopy(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            notification.textContent = 'Скопировано!';
            notification.classList.add('show');
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 2000);
        } catch (err) {
            notification.textContent = 'Ошибка копирования';
            notification.style.backgroundColor = '#f44336';
            notification.classList.add('show');
            
            setTimeout(() => {
                notification.classList.remove('show');
                notification.style.backgroundColor = '#4CAF50';
            }, 2000);
        }
        
        document.body.removeChild(textArea);
    }
});