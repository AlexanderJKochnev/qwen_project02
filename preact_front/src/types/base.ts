// src/types/base.ts

/**
 * Базовый интерфейс, соответствующий app/core/schemas/base.py → BaseModel
 */
export interface BaseModel {
  id: number;
}

/**
 * Локализованные текстовые поля (языки: en, ru, fr)
 */
export interface LangFields {
  name?: string;
  name_ru?: string;
  name_fr?: string;
  description?: string;
  description_ru?: string;
  description_fr?: string;
}

/**
 * Поля с датами (если понадобятся)
 */
export interface TimestampFields {
  created_at?: string; // ISO 8601
  updated_at?: string;
}

/**
 * Базовые схемы, соответствующие Pydantic
 */
export interface ReadSchema extends BaseModel, LangFields {}
export interface CreateSchema extends LangFields {
  name: string;
}
export interface UpdateSchema extends Partial<LangFields> {
  name?: string;
}

/**
 * Ответ с пагинацией (на будущее, но вы сказали — исключить пагинацию)
 * → пока не используем
 */
// export interface PaginatedResponse<T> {
//   items: T[];
//   total?: number;
//   page?: number;
//   page_size?: number;
// }

/**
 * Простой список (без пагинации) — это то, что возвращает /all
 */
export type ListResponse<T> = T[];

export interface PaginatedResponse<T> {
  items: T[];
  total?: number;
  page?: number;
  page_size?: number;
  has_next?: number;
  has_prev?: number;
}

export interface Anchor {
  page_offset: number;
  last_score: string; // передаем как string!
  last_id: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  anchors: Anchor[];
}