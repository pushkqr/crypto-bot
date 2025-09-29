
import sys
import warnings

from datetime import datetime

from crypto.crew import Crypto

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def get_timeframe_input():
    """Get timeframe from user input"""
    valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]
    
    print("\n📊 Select Trading Timeframe:")
    print("=" * 30)
    print("1. 1m  - 1 minute")
    print("2. 5m  - 5 minutes") 
    print("3. 15m - 15 minutes")
    print("4. 30m - 30 minutes")
    print("5. 1h  - 1 hour (default)")
    print("6. 2h  - 2 hours")
    print("7. 4h  - 4 hours")
    print("8. 6h  - 6 hours")
    print("9. 8h  - 8 hours")
    print("10. 12h - 12 hours")
    print("11. 1d  - 1 day")
    
    while True:
        try:
            choice = input(f"\n🤔 Enter your choice (1-13) or timeframe directly (e.g., '15m'): ").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= 13:
                    timeframe = valid_timeframes[choice_num - 1]
                    break
                else:
                    print("❌ Please enter a number between 1-13")
                    continue
            
            elif choice in valid_timeframes:
                timeframe = choice
                break
            else:
                print(f"❌ Invalid input. {', '.join(valid_timeframes)}")
                continue
                
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid input. Please try again.")
            continue
    
    return timeframe


def run():
    """
    Run the crew.
    """
    timeframe = get_timeframe_input()
    
    print(f"\n📊 Selected Timeframe: {timeframe}")
    print("=" * 40)
    
    inputs = {
        "date": datetime.today().strftime("%Y-%m-%d"),
        "timeframe": timeframe
    }
    
    try:
        Crypto().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


