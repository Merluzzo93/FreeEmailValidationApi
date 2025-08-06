from fastapi import FastAPI, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import EmailStr, BaseModel
from email_validator import validate_email
from typing import Union, List
from dotenv import load_dotenv
import os

# Load environment variables from .env (if any)
load_dotenv()

# FastAPI app configuration
description_of_fastapi = """
``Simple, reliable and free email validation API. Thanks to https://github.com/JoshData/python-email-validator``

### [📝 Test Now](/validate-email?email=user@example.com)

## Features
* Free, no limits
* Bulk validation (up to 10)
* Syntax, domain and deliverability checks
* Friendly error messages
* Supports international domains
"""

app = FastAPI(
    title="📨 Free Email Validation API",
    description=description_of_fastapi,
    contact={"url": "https://github.com/mehmetcanfarsak", "Name": "Mehmet Can Farsak"},
)

# Static and templates
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class EmailValidationResponseModel(BaseModel):
    is_email_valid: bool
    domain: Union[str, None] = None
    original_email: str
    local_part: Union[str, None] = None
    ascii_local_part: Union[str, None] = None
    ascii_domain: Union[str, None] = None
    smtputf8: Union[bool, None] = None
    mx: list = []
    spf: Union[str, None] = None
    ascii_email: Union[str, None] = None


class BulkEmailsModel(BaseModel):
    emails: List[EmailStr]


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/show-email-validation-form", include_in_schema=False, response_class=HTMLResponse)
def show_form(request: Request):
    return templates.TemplateResponse("show-email-validation-form.html", {"request": request})


@app.get("/validate-email", description="Validate Email", response_model=EmailValidationResponseModel,
         tags=["Validate Single Email"])
def validate_single_email(email: EmailStr = Query(example="user@example.com")):
    try:
        result = validate_email(email)
        return EmailValidationResponseModel(
            is_email_valid=True,
            domain=result.domain,
            original_email=result.original_email,
            local_part=result.local_part,
            ascii_local_part=result.ascii_local_part,
            ascii_domain=result.ascii_domain,
            smtputf8=result.smtputf8,
            mx=result.mx,
            spf=result.spf,
            ascii_email=result.ascii_email,
        )
    except Exception:
        return EmailValidationResponseModel(is_email_valid=False, original_email=email)


@app.post("/bulk-validate-emails", description="Bulk Validate Emails (max 10)",
          response_model=List[EmailValidationResponseModel], tags=["Bulk Validate"])
def bulk_validate_emails(emails: BulkEmailsModel):
    if len(emails.emails) > 10:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Max 10 emails can be validated.",
        )
    responses = []
    for email in emails.emails:
        try:
            result = validate_email(email)
            responses.append(EmailValidationResponseModel(
                is_email_valid=True,
                domain=result.domain,
                original_email=result.original_email,
                local_part=result.local_part,
                ascii_local_part=result.ascii_local_part,
                ascii_domain=result.ascii_domain,
                smtputf8=result.smtputf8,
                mx=result.mx,
                spf=result.spf,
                ascii_email=result.ascii_email,
            ))
        except Exception:
            responses.append(EmailValidationResponseModel(is_email_valid=False, original_email=email))
    return responses


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")
