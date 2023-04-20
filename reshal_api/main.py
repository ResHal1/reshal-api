from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def home():
    return {"message": "Reshal API"}


def run():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
