# app.core.utils.rembg_import.py
"""
    rembg очень сильно тормозит при начальнйо загрузке - поэтому вот так
"""
_rembg_remove = None
_rembg_new_session = None


def get_remove():
    global _rembg_remove
    if _rembg_remove is None:
        from rembg import remove
        _rembg_remove = remove
    return _rembg_remove


def get_new_session():
    global _rembg_new_session
    if _rembg_new_session is None:
        from rembg import new_session
        _rembg_new_session = new_session
    return _rembg_new_session