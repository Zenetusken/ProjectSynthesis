from pydantic import BaseModel, Field
from typing import Optional


class PATRequest(BaseModel):
    token: str = Field(..., min_length=1, description="GitHub Personal Access Token")


class RepoInfo(BaseModel):
    full_name: str
    name: str
    private: bool = False
    default_branch: str = "main"
    description: Optional[str] = None
    language: Optional[str] = None
    size_kb: int = 0


class LinkRepoRequest(BaseModel):
    full_name: str = Field(..., description="Repository full name (owner/repo)")
    branch: Optional[str] = Field(None, description="Branch name, defaults to repo default")


class LinkedRepoResponse(BaseModel):
    id: str
    full_name: str
    branch: str
    default_branch: Optional[str] = None
    language: Optional[str] = None
    linked_at: Optional[str] = None


class GitHubUserInfo(BaseModel):
    connected: bool = False
    login: Optional[str] = None
    avatar_url: Optional[str] = None
    github_user_id: Optional[int] = None
    token_type: Optional[str] = None
