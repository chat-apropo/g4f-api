import g4f
from fastapi import FastAPI, HTTPException

app = FastAPI(root_path="ai_api")

@app.get("/3")
def test(text: str):
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo-16k-0613",
            messages=[{"role": "user", "content": text}],
            stream=False)
    except:
        raise HTTPException(status_code=404, detail="insert crappy error handling message here lol :)")
    return {"message": response }
