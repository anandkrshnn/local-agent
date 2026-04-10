"""Utilities for localagent"""

import logging
import time
from typing import Any, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("localagent")

class TraceLogger:
    """Simple tracer for agent activities"""
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def thinking(self, message: str):
        if self.verbose:
            print(f"🤔 {message}")
            logger.debug(f"Thinking: {message}")

    def call(self, tool: str, args: Dict):
        if self.verbose:
            print(f"⚙️ Calling tool: {tool}")
            logger.debug(f"Tool call: {tool} with {args}")

    def error(self, message: str):
        print(f"❌ Error: {message}")
        logger.error(message)

    def success(self, message: str):
        print(f"✅ {message}")
        logger.info(message)
