from pydantic import BaseModel, ConfigDict

class CreatorBase(BaseModel):
    slug: str
    name: str
    description: str = ""
    image_url: str = ""
    download_url: str = ""

class CreatorCreate(CreatorBase):
    pass

class CreatorRead(CreatorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DownloadBase(BaseModel):
    slug: str
    title: str
    description: str = ""
    file_url: str = ""
    version: str = "1.0.0"

class DownloadCreate(DownloadBase):
    pass

class DownloadRead(DownloadBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ThemeBase(BaseModel):
    slug: str
    title: str
    description: str = ""
    preview_url: str = ""
    unlock_type: str = "free"

class ThemeCreate(ThemeBase):
    pass

class ThemeRead(ThemeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: str
    username: str
    role: str = "user"

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: str
    password: str