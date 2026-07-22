from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from greenledger.pipeline import run_pipeline

from .charts import render_trend_svg

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_BILLS_FOLDER = BASE_DIR.parent / "fixtures" / "bills"

app = FastAPI(title="GreenLedger Dashboard")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Rendered directly with jinja2's own Environment rather than FastAPI's
# Jinja2Templates wrapper: the installed starlette/jinja2 combo on this machine
# hits an internal template-cache bug ("cannot use 'tuple' as a dict key") inside
# starlette.templating's caching layer. Calling jinja2 directly sidesteps it.
_env = Environment(
    loader=FileSystemLoader(BASE_DIR / "templates"),
    autoescape=select_autoescape(["html"]),
)


def _render(template_name: str, **context) -> HTMLResponse:
    template = _env.get_template(template_name)
    return HTMLResponse(template.render(**context))


UTILITY_LABELS = {
    "electricity": "Electricity",
    "natural_gas": "Natural Gas",
    "water": "Water",
}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return _render("index.html", request=request, default_folder=str(DEFAULT_BILLS_FOLDER))


@app.post("/report", response_class=HTMLResponse)
@app.get("/report", response_class=HTMLResponse)
def report(request: Request, bills_folder: str = Form(default=str(DEFAULT_BILLS_FOLDER))):
    if request.method == "GET":
        bills_folder = request.query_params.get("bills_folder", str(DEFAULT_BILLS_FOLDER))

    folder = Path(bills_folder)
    if not folder.is_dir():
        return _render(
            "index.html",
            request=request,
            default_folder=str(DEFAULT_BILLS_FOLDER),
            error=f"'{bills_folder}' is not a directory on this machine.",
        )

    result = run_pipeline(folder)

    charts = {
        utility_type: render_trend_svg(result.trend_points, utility_type)
        for utility_type in UTILITY_LABELS
        if any(t.utility_type == utility_type for t in result.trend_points)
    }

    return _render(
        "report.html",
        request=request,
        folder=str(folder),
        result=result,
        charts=charts,
        utility_labels=UTILITY_LABELS,
    )
