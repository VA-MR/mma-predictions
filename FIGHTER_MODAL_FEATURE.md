# Fighter Modal Feature

## Описание
Добавлен новый функционал отображения детальной информации о бойце во всплывающем окне (modal) при клике на карточку бойца.

## Реализованные возможности

### Backend (API)
1. **Новый endpoint**: `GET /api/fighters/{fighter_id}`
   - Возвращает полную информацию о бойце по ID
   - Включает все метаданные и статистику из базы данных

2. **Файлы**:
   - `api/routes/fighters.py` - новый роутер для бойцов
   - `database/db.py` - добавлен метод `get_fighter_by_id()`
   - `api/main.py` - зарегистрирован fighters_router

### Frontend (React)
1. **Компонент FighterModal** (`frontend/src/components/FighterModal.tsx`)
   - Красивое модальное окно с детальной информацией о бойце
   - Анимации открытия/закрытия
   - Responsive дизайн
   - Отображает:
     * Основная информация (имя, рекорд, страна)
     * Физические данные (возраст, рост, вес, размах рук)
     * Боевой стиль
     * Методы побед (KO/TKO, сабмишны, решения)
     * Методы поражений
     * Ссылка на полный профиль

2. **Стилизация** (`frontend/src/components/FighterModal.css`)
   - Темный градиентный фон
   - Анимация появления
   - Backdrop с blur эффектом
   - Кастомный скроллбар
   - Адаптивный дизайн для мобильных устройств

3. **API клиент** (`frontend/src/api/client.ts`)
   - Добавлена функция `getFighter(id: number): Promise<Fighter>`

4. **Интеграция**:
   - **FightCard** (`frontend/src/components/FightCard.tsx`)
     * Карточки бойцов теперь кликабельны
     * Hover эффект для индикации кликабельности
     * При клике открывается модальное окно
   
   - **FightPage** (`frontend/src/pages/FightPage.tsx`)
     * Карточки бойцов в заголовке страницы боя кликабельны
     * Hover эффект
     * При клике открывается модальное окно

## Как использовать

### На странице событий
1. Перейдите на главную страницу
2. Нажмите на любую карточку бойца в списке боев
3. Откроется модальное окно с детальной информацией
4. Нажмите ✕ или кликните вне окна для закрытия

### На странице боя
1. Перейдите на страницу конкретного боя
2. Нажмите на карточку любого бойца в заголовке
3. Откроется модальное окно с детальной информацией

## Технические детали

### Структура данных Fighter
```typescript
interface Fighter {
  id: number;
  name: string;
  name_english: string | null;
  country: string | null;
  wins: number;
  losses: number;
  draws: number;
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  reach_cm: number | null;
  style: string | null;
  weight_class: string | null;
  ranking: string | null;
  wins_ko_tko: number | null;
  wins_submission: number | null;
  wins_decision: number | null;
  losses_ko_tko: number | null;
  losses_submission: number | null;
  losses_decision: number | null;
  profile_url: string | null;
  profile_scraped: boolean;
  record: string;
}
```

### API Endpoint
```
GET /api/fighters/{fighter_id}

Response: Fighter (JSON)
Status: 200 OK / 404 Not Found
```

## Особенности реализации

1. **Предотвращение навигации**: При клике на карточку бойца событие останавливается (`stopPropagation`), чтобы не переходить на страницу боя

2. **Lazy loading**: Данные бойца загружаются только при открытии модального окна

3. **Обработка ошибок**: Если данные не загрузились, показывается сообщение об ошибке

4. **Accessibility**: Модальное окно можно закрыть кликом вне его области или по кнопке закрытия

5. **Анимации**: Используется `framer-motion` для плавных анимаций открытия/закрытия

## Возможные улучшения в будущем

- [ ] Добавить историю боев бойца
- [ ] Показать статистику против разных типов соперников
- [ ] Добавить фото/аватар бойца
- [ ] Показать тренд формы (последние бои)
- [ ] Добавить графики статистики
- [ ] Интеграция с внешними API для получения дополнительных данных

## Дата добавления
3 декабря 2025

## Автор
Реализовано в рамках проекта MMA Scoring Application

