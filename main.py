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


def anonymize_content(text: str, mode: str = 'default'):
    results = analyzer.analyze(text=text, language='en')

    operator_config = None
    if mode == 'mask':
        operator_config = {"DEFAULT": OperatorConfig("replace", {"new_value": "***"})}

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
async def anonymize_text(request: Request, text: str = Form(...), mode: str = Form('default')):
    anonymized_text = anonymize_content(text, mode)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "anonymized_text": anonymized_text,
        "input_text": text,
        "mode": mode,
        "active_tab": "text"
    })


@app.post("/anonymize_csv")
async def anonymize_csv(request: Request, file: UploadFile = File(...), mode: str = Form('default')):
    contents = await file.read()
    csv_text = contents.decode('utf-8')

    anonymized_text = anonymize_content(csv_text, mode)

    output_io = io.StringIO(anonymized_text)
    response = StreamingResponse(output_io, media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=anonymized_{file.filename}"
    return response
