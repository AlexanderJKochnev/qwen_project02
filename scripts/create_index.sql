-- create_index.sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS drink_trigram_idx_combined
ON drinks
USING gin (
    (
        coalesce(title, '') || ' ' ||
        coalesce(title_ru, '') || ' ' ||
        coalesce(title_fr, '') || ' ' ||
        coalesce(title_cn, '') || ' ' ||
        coalesce(title_es, '') || ' ' ||
        coalesce(subtitle, '') || ' ' ||
        coalesce(subtitle_ru, '') || ' ' ||
        coalesce(subtitle_fr, '') || ' ' ||
        coalesce(subtitle_cn, '') || ' ' ||
        coalesce(subtitle_es, '') || ' ' ||
        coalesce(description, '') || ' ' ||
        coalesce(description_ru, '') || ' ' ||
        coalesce(description_fr, '') || ' ' ||
        coalesce(description_cn, '') || ' ' ||
        coalesce(description_es, '') || ' ' ||
        coalesce(recommendation, '') || ' ' ||
        coalesce(recommendation_ru, '') || ' ' ||
        coalesce(recommendation_fr, '') || ' ' ||
        coalesce(recommendation_cn, '') || ' ' ||
        coalesce(recommendation_es, '') || ' ' ||
        coalesce(madeof, '') || ' ' ||
        coalesce(madeof_ru, '') || ' ' ||
        coalesce(madeof_fr, '')
        coalesce(madeof_cn, '')
        coalesce(madeof_es, '')
    )
    gin_trgm_ops
);