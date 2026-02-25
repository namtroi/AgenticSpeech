import os
from supabase import create_client, Client

# Lazy initialization of the Supabase client
_supabase_client = None


def get_supabase_client() -> Client:
    """
    Returns a configured Supabase client using the URL and SERVICE_ROLE_KEY
    from the environment. The Service Role Key allows the backend to bypass RLS
    for bulk ingestion inserts.
    """
    global _supabase_client
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            raise RuntimeError(
                "Missing Supabase credentials. Ensure SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY are set in the environment."
            )

        _supabase_client = create_client(url, key)

    return _supabase_client
