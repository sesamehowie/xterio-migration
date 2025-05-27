import json
from loguru import logger


def read_txt(filename):
    try:
        with open(filename, "r") as f:
            data = f.read().splitlines()
        return data
    except Exception as e:
        logger.warning(f"Couldnt load content from {filename}: {str(e)}")
        return []


def read_json(filename):
    try:
        data = json.load(open(filename))
        return data
    except Exception as e:
        logger.warning(f"Could read from {filename}: {str(e)}")
        return {}
