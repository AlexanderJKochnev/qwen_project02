from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select, insert, update


def upgrade():
    # Описываем таблицы для SQL выражений
    subregions_t = table('subregions', column('id', sa.Integer))
    sites_t = table(
        'sites', column('id', sa.Integer), column('subregion_id', sa.Integer),
        column('name', sa.String)
    )
    drinks_t = table(
        'drinks', column('id', sa.Integer), column('subregion_id', sa.Integer), column('site_id', sa.Integer)
    )

    # 1. Создаем записи в Site для каждого Subregion
    op.execute(
        insert(sites_t).from_select(
            ['subregion_id', 'name'], select(subregions_t.c.id, sa.null())
        )
    )

    # 2. Добавляем колонку site_id в Drink
    op.add_column('drinks', sa.Column('site_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_drinks_site_id_sites', 'drinks', 'sites', ['site_id'], ['id'])

    # 3. Переносим связь: Drink -> Site (через subregion_id)
    subquery = (select(sites_t.c.id).where(sites_t.c.subregion_id == drinks_t.c.subregion_id).scalar_subquery())
    op.execute(update(drinks_t).values(site_id=subquery))

    # 4. Удаляем старую колонку и её FK
    # ВНИМАНИЕ: Проверь имя drinks_subregion_id_fkey в БД!
    op.drop_constraint('drinks_subregion_id_fkey', 'drinks', type_='foreignkey')
    op.drop_column('drinks', 'subregion_id')

    # 5. Делаем новую колонку обязательной
    op.alter_column('drinks', 'site_id', nullable=False)


def downgrade():
    # Таблицы для отката
    sites_t = table(
        'sites', column('id', sa.Integer), column('subregion_id', sa.Integer)
    )
    drinks_t = table(
        'drinks', column('id', sa.Integer), column('subregion_id', sa.Integer), column('site_id', sa.Integer)
    )

    # 1. Возвращаем колонку subregion_id в Drink
    op.add_column('drinks', sa.Column('subregion_id', sa.Integer(), nullable=True))

    # 2. Восстанавливаем данные: Drink.subregion_id = Site.subregion_id
    subquery = (select(sites_t.c.subregion_id).where(sites_t.c.id == drinks_t.c.site_id).scalar_subquery())
    op.execute(update(drinks_t).values(subregion_id=subquery))

    # 3. Возвращаем Foreign Key и Not Null
    op.create_foreign_key('drinks_subregion_id_fkey', 'drinks', 'subregions', ['subregion_id'], ['id'])
    op.alter_column('drinks', 'subregion_id', nullable=False)

    # 4. Удаляем связь с Site и саму колонку site_id
    op.drop_constraint('fk_drinks_site_id_sites', 'drinks', type_='foreignkey')
    op.drop_column('drinks', 'site_id')

    # 5. Очищаем таблицу sites (удаляем временные записи)
    # Осторожно: это удалит ВСЕ записи в Site.
    # Если там были полезные данные, нужно добавить WHERE.
    op.execute(sites_t.delete())
