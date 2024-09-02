import asyncio
from scripts import rightmove
import os


ROOT_DIR = os.getcwd()


if __name__ == "__main__":
    # asyncio.run(cleaning.run_clean())
    asyncio.run(rightmove.main())
