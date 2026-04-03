# Интеграция с GigaChat

## Подключение

Для использования GigaChat в проекте необходимо:

1. Получить ключ авторизации в [личном кабинете GigaChat](https://developers.sber.ru/studio).
2. Добавить в `backend/.env`:

```env
LLM_MODE=gigachat
IMAGE_MODE=gigachat
GIGACHAT_CREDENTIALS=<ваш_ключ_авторизации>
```

## TLS-сертификат

Для работы с GigaChat API может потребоваться корневой сертификат Минцифры.

- Инструкция по установке: <https://developers.sber.ru/docs/gigachat/certificates>
- Общая документация API: <https://developers.sber.ru/docs/gigachat>

Для локального демо можно временно отключить проверку сертификата:

```env
GIGACHAT_VERIFY_SSL_CERTS=false
```

Использовать это значение в постоянной среде не рекомендуется.

## Что ещё проверить

- `GIGACHAT_CREDENTIALS` задан в `backend/.env`, а сам файл не попал в Git.
- Для текстовой генерации выставлен `LLM_MODE=gigachat`.
- Для генерации изображений выставлен `IMAGE_MODE=gigachat`.
- При необходимости можно прогнать smoke-test: `scripts\run_gigachat_smoke.cmd`.
