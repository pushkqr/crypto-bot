#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from crypto.crew import Crypto

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    # inputs = {
    #     'topic': 'AI LLMs',
    #     'current_year': str(datetime.now().year)
    # }
    
    try:
        Crypto().crew().kickoff()
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


