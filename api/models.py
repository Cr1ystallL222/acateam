from pydantic import BaseModel

class AuthVerifyRequest(BaseModel):
    session_id: str
    code: str

class AuthDraftRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str
    consent_pd: bool
    consent_marketing: bool

class RegisterRequest(BaseModel):
    session_id: str
    first_name: str
    last_name: str
    phone: str
    email: str
    consent_terms: bool
    consent_pd: bool

class PaymentRequest(BaseModel):
    movie: str
    session_time: str
    qty: int
