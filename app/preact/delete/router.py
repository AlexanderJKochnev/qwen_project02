# app/preact/delete/router.py
from fastapi import Request, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.preact.core.router import PreactRouter
from app.core.config.database.db_async import get_db
from app.core.schemas.base import DeleteResponse


class DeleteRouter(PreactRouter):
    def __init__(self):
        super().__init__(prefix='delete', method='DELETE', tier=2)

    def __source_generator__(self, source: dict):
        """
            генератор для создания роутов
        """
        return ((f'/{key}' + '/{id}', DeleteResponse, None) for key, val in source.items())

    async def endpoint(self, request: Request, id: int, background_tasks: BackgroundTasks,
                       session: AsyncSession = Depends(get_db)) -> DeleteResponse:
        """
            Удаление одной записи по id
        """
        current_path = request.url.path
        pref, _ = self.__path_decoder__(current_path, 2)
        model = self.source.get(pref)
        repo = self.get_repo(model)
        service = self.get_service(model)
        result = await service.delete(id, model, repo, background_tasks, session)
        if not result.get('success'):
            error_message = result.get('message', 'Unknown error')
            # Для Foreign Key violation возвращаем 400 Bad Request
            if 'невозможно удалить запись: на неё ссылаются другие объекты' in error_message:
                raise HTTPException(status_code=400, detail=error_message)
            # Для других ошибок базы данных возвращаем 500
            elif 'ошибка базы данных' in error_message.lower():
                raise HTTPException(status_code=500, detail=error_message)
            # Для "не найдена" возвращаем 404
            elif 'не найдена' in error_message:
                raise HTTPException(status_code=404, detail=error_message)
            else:
                raise HTTPException(status_code=500, detail=error_message)
        return DeleteResponse(**result)
