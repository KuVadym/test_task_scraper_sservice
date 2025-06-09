from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi import APIRouter

from app.models import ApiResponse
from app.decrypt_data import decrypt_data
from database import form_repository


save_to_db_apir = APIRouter()


@save_to_db_apir.post("/api/add_users", response_model=ApiResponse)
async def add_users_data(request: Request, encrypt:bool = False):
    try:
        data = await request.json()

        if encrypt:
            data = decrypt_data(data)
        
        if not data:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "No data provided",
                    "processed": 0,
                    "success": 0,
                    "errors": ["Empty request body"]
                }
            )
        
        if not isinstance(data, dict):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Invalid data format. Expected dictionary",
                    "processed": 0,
                    "success": 0,
                    "errors": ["Invalid data format"]
                }
            )
        
        result = form_repository.add_form_data_to_db(data)
        
        return {
            "status": "success",
            "message": "Data processed successfully",
            "processed": result.get("processed", 0),
            "success": result.get("created", 0) + result.get("updated", 0),
            "errors": result.get("errors", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")