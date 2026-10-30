from pydantic import BaseModel,Field

class MfaVerifyRequest(BaseModel):
    code:str=Field(...,min_length=6,max_length=6)

class MfaSetupResponse(BaseModel):
    provisioning_uri:str
    secret:str

class MfaChallengeRequest(BaseModel):
    challenge_token:str
    code:str=Field(...,min_length=6,max_length=6)

class MfaLoginRequiredResponse(BaseModel):
    mfa_required:bool
    challenge_token:str
    access_token:str
    refresh_token:str
    token_type:str