"""Create a ready-to-use test user.

Usage: python scripts/create_test_user.py [email]

In mock auth mode the user is created directly in the local database with a
generated password. In supabase mode the Supabase service-role key is used via
the admin API. The service-role key must NEVER be shared with frontend
developers; keep this script server-side only.
"""

import asyncio
import secrets
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.models.catalog import UserEquipment  # noqa: E402
from app.db.session import async_session_factory  # noqa: E402
from app.repositories.catalog import CatalogRepository  # noqa: E402
from app.repositories.profiles import ProfileRepository  # noqa: E402


async def create_test_user(email: str) -> None:
    async with async_session_factory() as session:
        profiles = ProfileRepository(session)

        auth_user_id = uuid.uuid4()
        password = None

        if settings.auth_mode == "mock":
            password = secrets.token_urlsafe(12)
            await profiles.create_auth_user(email, hash_password(password))
        else:
            import httpx

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users",
                    headers={
                        "apikey": settings.supabase_service_role_key,
                        "Authorization": f"Bearer {settings.supabase_service_role_key}",
                    },
                    json={
                        "email": email,
                        "password": secrets.token_urlsafe(12),
                        "email_confirm": True,
                    },
                )
                resp.raise_for_status()
                auth_user_id = uuid.UUID(resp.json()["id"])
                password = "(set by Supabase admin call)"

        profile = await profiles.get_by_auth_user_id(auth_user_id)
        if profile is None:
            profile = await profiles.create(auth_user_id, email)

        catalog = CatalogRepository(session)
        equipment_ids = [
            e.id for e in await catalog.list_equipment() if e.slug in ("dumbbells", "bench")
        ]
        for equipment_id in equipment_ids:
            session.add(UserEquipment(user_id=profile.id, equipment_id=equipment_id))
        await session.commit()

        print("Test user ready:")
        print(f"  email:    {email}")
        if password:
            print(f"  password: {password}")
        print(f"  profile:  {profile.id}")
        print("Remember: email confirmation may be required in supabase mode.")


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else f"testuser+{secrets.token_hex(4)}@example.com"
    asyncio.run(create_test_user(email))
