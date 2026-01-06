import logging

def init_logging(app):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    app.logger.info("Application started")
