from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import io

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def decrypt_content(text: str, key: str) -> str:
    import re
    from presidio_anonymizer.operators import Decrypt

    def find_base64_strings(text):
        base64_pattern = r'(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?'
        matches = re.findall(base64_pattern, text)
        matches = [m for m in matches if len(m) >= 44]
        return matches

    base64_strings = find_base64_strings(text)
    for base64_string in base64_strings:
        try:
            decrypted_result = Decrypt().operate(text=base64_string, params={"key": key})
            text = text.replace(base64_string, decrypted_result)
        except Exception as e:
            print(f"Error decrypting: {base64_string} - {e}")
    return text


def anonymize_content(text: str, mode: str = 'default', key: str = None):
    if mode == 'decrypt':
        if not key:
            raise ValueError("Decryption key is required for decrypt mode.")
        decrypted_text = decrypt_content(text, key)
        return decrypted_text
    else:
        results = analyzer.analyze(text=text, language='en')

        if mode == 'mask':
            operator_config = {"DEFAULT": OperatorConfig("replace", {"new_value": "***"})}
        elif mode == 'encrypt':
            if not key:
                raise ValueError("Encryption key is required for encrypt mode.")
            operator_config = {"DEFAULT": OperatorConfig("encrypt", {"key": key})}
        else:
            operator_config = None

        if operator_config:
            anonymized_result = anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=operator_config
            )
        else:
            anonymized_result = anonymizer.anonymize(
                text=text,
                analyzer_results=results
            )

        return anonymized_result.text


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_tab": "text"
    })


@app.post("/anonymize_text", response_class=HTMLResponse)
async def anonymize_text(request: Request, text: str = Form(...), mode: str = Form('default'), key: str = Form(None)):
    try:
        anonymized_text = anonymize_content(text, mode, key)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "anonymized_text": anonymized_text,
            "input_text": text,
            "mode": mode,
            "key": key,
            "active_tab": "text"
        })
    except Exception as e:
        error_message = str(e)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "input_text": text,
            "mode": mode,
            "key": key,
            "error_message": error_message,
            "active_tab": "text"
        })


@app.post("/anonymize_csv")
async def anonymize_csv(request: Request, file: UploadFile = File(...), mode: str = Form('default'), key: str = Form(None)):
    try:
        contents = await file.read()
        csv_text = contents.decode('utf-8')

        anonymized_text = anonymize_content(csv_text, mode, key)

        output_io = io.StringIO(anonymized_text)
        response = StreamingResponse(output_io, media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=processed_{file.filename}"
        return response
    except Exception as e:
        error_message = str(e)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error_message": error_message,
            "mode": mode,
            "key": key,
            "active_tab": "csv"
        })
