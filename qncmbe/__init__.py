import sys
import logging

logger = logging.getLogger(__name__)

if len(logging.getLogger().handlers) == 0:
    logging.basicConfig(
        format='%(levelname)s (%(name)s): %(message)s',
        level=logging.INFO,
        stream=sys.stdout
    )
