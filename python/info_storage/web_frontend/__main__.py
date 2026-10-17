import os

from python.info_storage.web_frontend.app import create_app

if __name__ == "__main__":
    create_app().run(
        host=os.getenv("INFOSTORAGE_FRONTEND_HOST", "127.0.0.1"),
        port=int(os.getenv("INFOSTORAGE_FRONTEND_PORT", "5000")),
        debug=False,
    )
