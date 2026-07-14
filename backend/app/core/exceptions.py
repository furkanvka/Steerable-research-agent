from fastapi import HTTPException

class PipelineException(HTTPException):
    def __init__(self, status_code: int, stage: str, message: str, details: str):
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "stage": stage,
                "message": message,
                "details": details
            }
        )
