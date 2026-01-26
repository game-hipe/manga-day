# Manga-Day Новая манга в 2 клика!
В чём суть проекта? У меня есть много сайтов, где манга выходит не каждый день, но следит за ними нужно, поэтому я подумал почему-бы не просто создать пауков, и ТГ админку? Вот на этом и решили!

## Как запустить проект?
```bash
git clone https://github.com/game-hipe/manga-day.git
cd manga-day
cp configuration-example.yaml > config.yaml

nano configu.yaml # Вставтье ваш бот токен, для работы.

docker-compose build --no-cache
docker-compose up -d
```

## 2 Способ через прямой python (python3.13.X+)
```bash
git clone https://github.com/game-hipe/manga-day.git
cd manga-day
cp configuration-example.yaml > config.yaml

nano config.yaml # Вставтье ваш бот токен, для работы.
pip install -r requirements.txt
python main.py
```

> [!WARNING]
> Проект является просто демонстрацие своих сил в BackEnd, и в ТГ ботах, поэтому не бейте тапком

> [!WARNING]
> На данный момент, готово только 2 паука, и так-же ТГ админка не готова!