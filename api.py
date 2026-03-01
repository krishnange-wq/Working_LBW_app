from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import numpy as np
import json
import os
import main  # Your main.py

app = FastAPI()

@app.post("/analyze")
async def analyze_lbw(
    video: UploadFile = File(...),
    corners_json: str = Form(...)
):
    # 1. Save the incoming video
    temp_path = f"temp_{video.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(await video.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save error: {e}")

    # 2. Convert the corners string back into a list/array
    try:
        corners_list = json.loads(corners_json)
        user_corners = np.array(corners_list, dtype=np.float32)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid corner data")

    # 3. Call the Brain (Main.py)
    # Ensure your 'run_mobile_backend' function matches these two inputs!
    try:
        result = main.run_mobile_backend(temp_path, user_corners)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logic Crash: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)