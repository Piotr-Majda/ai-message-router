import logging

def setup_logging(name: str):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    logger= logging.getLogger(name)
    return logger 