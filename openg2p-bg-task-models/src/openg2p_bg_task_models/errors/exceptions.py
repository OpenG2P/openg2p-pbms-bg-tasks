from typing import Optional

from .codes import EEEErrorCodes


class EEEException(Exception):
    def __init__(
        self,
        code: EEEErrorCodes,
        eee_payload: Optional[object] = None,
        message: Optional[str] = None,
    ):
        self.code: EEEErrorCodes = code
        self.message: Optional[str] = message
        self.eee_payload: object = eee_payload
        super().__init__(code, self.message)
