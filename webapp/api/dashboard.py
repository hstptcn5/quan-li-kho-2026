# -*- coding: utf-8 -*-
"""GET /api/dashboard: dữ liệu màn hình Tổng quan (chỉ đọc, scope local)."""

from __future__ import annotations

from webapp.routing import SCOPE_LOCAL, HttpError, Request, Response, Router, json_response
from webapp.services.dashboard import DEFAULT_LIMIT, build_dashboard_payload, validate_dashboard_params


def make_handler(db_factory):
    def handler(request: Request) -> Response:
        flt = request.query.get("filter", "all")
        limit = DEFAULT_LIMIT
        raw_limit = request.query.get("limit")
        if raw_limit is not None:
            try:
                limit = int(raw_limit)
            except ValueError:
                raise HttpError(400, "Tham số limit phải là số nguyên")
        try:
            validate_dashboard_params(flt, limit)
        except ValueError as exc:
            raise HttpError(400, str(exc))

        db = db_factory()
        try:
            payload = build_dashboard_payload(db, flt=flt, limit=limit)
        finally:
            db.conn.close()
        payload["success"] = True
        return json_response(payload)

    return handler


def register(router: Router, db_factory) -> None:
    router.add("GET", "/api/dashboard", make_handler(db_factory), scopes=(SCOPE_LOCAL,))
