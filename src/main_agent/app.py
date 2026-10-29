import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting app")
    logger.info("This is main agent ThoughtMate")


if __name__ == "__main__":
    main()
