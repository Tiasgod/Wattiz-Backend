"""
app/services/user_service.py
─────────────────────────────
Camada de serviço para operações de usuário.
Isola a lógica de negócio dos endpoints HTTP.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: UserCreate) -> User:
        """Cria um novo usuário com senha hasheada."""
        existing = await self.get_by_email(data.email)
        if existing:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado.",
            )
        user = User(
            name=data.name,
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
        )
        self.db.add(user)
        await self.db.flush()  # obtém o ID antes do commit
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Valida credenciais e retorna o usuário ou None."""
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def update(self, user: User, data: UserUpdate) -> User:
        if data.name is not None:
            user.name = data.name
        if data.email is not None:
            existing = await self.get_by_email(data.email)
            if existing and existing.id != user.id:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="E-mail já em uso.",
                )
            user.email = data.email.lower()
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.flush()
