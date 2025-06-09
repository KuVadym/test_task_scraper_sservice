class APIError(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"APIError {status_code}: {detail}")

class NotFoundError(APIError):
    def __init__(self, detail="Resource not found"):
        super().__init__(404, detail)
