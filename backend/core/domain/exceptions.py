from collections.abc import Mapping
from typing import Any


class GiroException(Exception):
    code = 'BUSINESS_RULE_VIOLATION'
    status_code = 400
    default_detail = 'A operação não pode ser concluída.'

    def __init__(
        self,
        detail: str | None = None,
        *,
        fields: Mapping[str, Any] | None = None,
    ) -> None:
        self.detail = detail or self.default_detail
        self.fields = dict(fields or {})
        super().__init__(self.detail)
