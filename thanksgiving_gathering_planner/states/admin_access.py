import reflex as rx

import asyncio
import logging

from reflex_enterprise.auth import AuthContext
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from thanksgiving_gathering_planner.models import AdminOwner


async def is_admin(ctx: AuthContext) -> bool:
    sub = ctx.auth_user_state.userinfo.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        return False
    try:
        async with asyncio.timeout(4):
            async with rx.asession() as session:
                owner_sub = await session.scalar(
                    select(AdminOwner.sub).where(AdminOwner.id == 1)
                )
        return owner_sub == sub
    except (SQLAlchemyError, OSError, TimeoutError):
        logging.exception("Unable to verify admin access")
        return False
