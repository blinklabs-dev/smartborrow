from pydantic import BaseModel
from typing import Optional, List

# Snowflake Connection Schemas
class SnowflakeConnectionBase(BaseModel):
    account_name: str
    username: str
    role: Optional[str] = None
    warehouse: Optional[str] = None

class SnowflakeConnectionCreate(SnowflakeConnectionBase):
    password: str

class SnowflakeConnection(SnowflakeConnectionBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

# User Schemas
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    snowflake_connections: List[SnowflakeConnection] = []

    class Config:
        orm_mode = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
