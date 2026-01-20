## GitHub Container Registry (GHCR)

1. Бесплатный уровень: Для публичных образов сервис бесплатен. Для приватных образов на бесплатных аккаунтах обычно предоставляется 500 МБ хранилища и 1 ГБ трафика в месяц.
2. Интеграция: Образы можно привязывать к конкретным репозиториям, что упрощает управление правами доступа.
3. Безопасность: Доступ осуществляется через персональные токены доступа (PAT) или стандартный GITHUB_TOKEN в рамках GitHub Actions. 
4. Инструкция по созданию PAT (Classic) в 2026 году:

    Войдите в GitHub и нажмите на свой аватар в правом верхнем углу.
    Перейдите в Settings (Настройки).
    В левом боковом меню в самом низу выберите Developer settings.
    Раскройте пункт Personal access tokens и выберите Tokens (classic).
    Нажмите кнопку Generate new token -> Generate new token (classic).
    Настройте токен:
        Note: Напишите название (например, docker-ghcr-token).
        Expiration: Установите срок действия (рекомендуется не более 90 дней для безопасности).
        Select scopes: Обязательно отметьте галочки write:packages (автоматически выберет read:packages) и repo (если образы привязаны к приватным репозиториям).
    Нажмите Generate token внизу страницы.
    Скопируйте токен сразу! После того как вы закроете страницу, он станет недоступен для просмотра.
5. Авторизация:
   1. cat /Users/kochnev/git/filesxxx.txt | docker login ghcr.io -u AlexanderJKochnev --password-stdin
   2. linux
      1. cd dockers/ghcr
      2. cat filesxxx.txt | docker login ghcr.io -u alexanderjkochnev --password-stdin
6. Тестирование и push образов
   1. docker pull postgres:alpine
   2. docker tag postgres:alpine ghcr.io/alexanderjkochnev/postgres:17-alpine
   3. docker push ghcr.io/alexanderjkochnev/postgres:17-alpine
7. Использование в Docker Compose:
   1. image: ghcr.io/alexanderjkochnev/my-postgres:alpine
8. 