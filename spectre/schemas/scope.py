from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class RepoScope(BaseModel):
    name: str
    description: str = ""
    allowed_repos: list[str] = Field(min_length=1)
    allowed_branches: list[str] = Field(default_factory=lambda: ["main"])
    include_paths: list[str] = Field(default_factory=lambda: ["**"])
    exclude_paths: list[str] = Field(
        default_factory=lambda: ["node_modules/**", "dist/**", ".git/**"]
    )
    max_commits_depth: int = Field(default=50, ge=1)
    max_duration_minutes: int = Field(default=30, ge=1)
    authorization: str = "owner-confirmed"

    @field_validator("allowed_repos")
    @classmethod
    def validate_repo_slugs(cls, values: list[str]) -> list[str]:
        for slug in values:
            if "/" not in slug or slug.count("/") != 1:
                raise ValueError(f"invalid repo slug: {slug}")
            owner, repo = slug.split("/", 1)
            if not owner or not repo:
                raise ValueError(f"invalid repo slug: {slug}")
        return values

    @classmethod
    def load(cls, path: Path) -> "RepoScope":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"invalid scope file: {path}")
        return cls.model_validate(data)

    def allows_repo(self, slug: str) -> bool:
        return slug in self.allowed_repos

    def allows_branch(self, branch: str) -> bool:
        return branch in self.allowed_branches
