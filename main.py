from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.post("/application-log")
async def receive_log(request: Request):
    # debug info
    print("---- New request ----")
    print("full url:", str(request.url))
    print("headers:", dict(request.headers))

    # try parse JSON
    try:
        data = await request.json()
        if data: 
            print("parsed JSON body:", data)
            return {"ok": True, "source": "json", "data": data}
    except Exception as e:
        print("no JSON or invalid JSON:", repr(e))

    # try form data (application/x-www-form-urlencoded or multipart)
    try:
        form = await request.form()
        if form:
            data = dict(form)
            print("parsed form data:", data)
            return {"ok": True, "source": "form", "data": data}
    except Exception as e:
        print("no form body:", repr(e))

    # raw body (for debugging)
    raw = await request.body()
    if raw:
        raw_text = raw.decode("utf-8", errors="replace")
        print("raw body (decoded):", raw_text)
        # attempt to parse raw text as JSON
        try:
            import json
            data = json.loads(raw_text)
            print("parsed JSON from raw body:", data)
            return {"ok": True, "source": "raw-json", "data": data}
        except Exception:
            return {"ok": True, "source": "raw", "raw": raw_text}

    # fallback to query params
    query = dict(request.query_params)
    print("query params:", query)
    if query:
        return {"ok": True, "source": "query", "data": query}

    # nothing found
    raise HTTPException(status_code=400, detail="Invalid or empty request. Send JSON body, form data, or query params.")
