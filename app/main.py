from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.processor import process_pdf
from typing import Literal
import uuid

app = FastAPI()

@app.post("/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    response_type: Literal["json", "excel"] = "json"
):
    try:
        file_bytes = await file.read()
        json_data, excel_output = process_pdf(file_bytes)

        if response_type == "excel":
            filename = f"converted_{uuid.uuid4().hex[:8]}.xlsx"
            return StreamingResponse(
                excel_output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            return JSONResponse(content=json_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
