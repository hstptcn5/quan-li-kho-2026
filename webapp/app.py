# -*- coding: utf-8 -*-
"""Ghép các endpoint thành một Router."""

from __future__ import annotations

from webapp.api import dashboard as dashboard_api
from webapp.routing import Router


def build_router(db_factory) -> Router:
    """``db_factory``: hàm không tham số trả về một ``DB`` mới (mỗi request một kết nối)."""
    router = Router()
    dashboard_api.register(router, db_factory)
    return router
