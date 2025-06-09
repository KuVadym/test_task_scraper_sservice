from fastapi import FastAPI
from intermediary_service.app.api.endpoints import router

app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    # category = 'SALE > Shop Deals > Hat Sale'
    # parser_script(category)
    app.run(host="0.0.0.0", port=5000, debug=True)