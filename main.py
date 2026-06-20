"""
Main Entry Point
Purpose: Coordinates the execution of the Scout, Analyst, Writer, Publisher,
         and Trend Extractor agents.
"""

from agents.scout import run_scout
from agents.analyst import run_analyst
from agents.writer import run_writer
from agents.publisher import run_publisher
from agents.trend_extractor import run_trend_extractor

def main():
    print("Running Scout...")
    run_scout()
    
    print("Running Analyst...")
    run_analyst()
    print("Running Writer...")
    run_writer()
    
    print("Running Publisher...")
    run_publisher()

    print("Running Trend Extractor...")
    run_trend_extractor()

if __name__ == "__main__":
    main()

