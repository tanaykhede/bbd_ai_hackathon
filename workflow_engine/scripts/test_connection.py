import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url


def mask_url(url_str: str) -> str:
    try:
        u = make_url(url_str)
        if u.password:
            # mask password
            return u.set(password="***").render_as_string(hide_password=False)
        return url_str
    except Exception:
        return url_str


def main():
    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = os.getenv("SQLALCHEMY_DATABASE_URL") or os.getenv("DATABASE_URL")

    if not url:
        print("ERROR: Provide DB URL as argv[1] or set SQLALCHEMY_DATABASE_URL/DATABASE_URL.")
        sys.exit(2)

    print(f"Connecting to: {mask_url(url)}")
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        dbinfo = conn.execute(text(
            "select current_database() as db, current_user as usr, inet_server_addr() as host, inet_server_port() as port, version() as ver"
        )).mappings().first()
        search_path = conn.execute(text("select current_setting('search_path') as sp"))
        search_path = next(search_path).sp
        current_schema = conn.execute(text("select current_schema() as cs"))
        current_schema = next(current_schema).cs
        print("OK: Connected")
        print(f"- database: {dbinfo['db']}")
        print(f"- user: {dbinfo['usr']}")
        print(f"- host: {dbinfo['host']}:{dbinfo['port']}")
        print(f"- server: {dbinfo['ver'].splitlines()[0]}")
        print(f"- search_path: {search_path}")
        print(f"- current_schema: {current_schema}")


if __name__ == "__main__":
    main()
