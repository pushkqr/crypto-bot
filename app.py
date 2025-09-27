import os
import json
import sys
import subprocess
from pathlib import Path
from bot import main as run_trading_main
import asyncio

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

def load_strategy():
    """Load existing strategy from output/backtest_results.json"""
    strategy_file = Path("output/backtest_results.json")
    
    if not strategy_file.exists():
        print("❌ No strategy file found")
        return None
    
    try:
        with open(strategy_file, 'r') as f:
            data = json.load(f)
        
        if 'strategy' not in data:
            print("❌ Invalid strategy file format")
            return None
        
        return data
        
    except Exception as e:
        print(f"❌ Error reading strategy file: {e}")
        return None

def run_crewai_workflow():
    """Run the CrewAI workflow to generate a new strategy"""
    print("\n🚀 Running CrewAI workflow to generate new strategy...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["uv", "run", "run_crew"], 
            capture_output=not DEBUG,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print("✅ CrewAI workflow completed successfully")
            return True
        else:
            print("❌ CrewAI workflow failed")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ CrewAI workflow timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running CrewAI workflow: {e}")
        return False

def run_trading_bot():
    """Run the trading bot"""
    print("\n🤖 Starting trading bot...")
    print("=" * 60)
    
    try:
        asyncio.run(run_trading_main())
    except KeyboardInterrupt:
        print("\n🛑 Trading bot stopped by user")
    except Exception as e:
        print(f"❌ Error running trading bot: {e}")

def main():
    """Main pipeline function"""
    print("🚀 Crypto Trading Bot")
    print("=" * 40)
    
    if not Path("bot.py").exists():
        print("❌ Please run this from the crypto project directory")
        sys.exit(1)
    
    data = load_strategy()
    strategy = data.get('strategy', {})
    performance = data.get('performance', {})
    
    if strategy:
        strategy_name = strategy.get('strategy_id', 'Unknown')
        coin_symbol = strategy.get('coin_symbol', 'Unknown')
        win_rate = performance.get('win_rate', 0)
        total_return = performance.get('total_return', 0)
        
        print(f"\n📋 Found existing strategy:")
        print(f"   Name: {strategy_name}")
        print(f"   Symbol: {coin_symbol}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Total Return: {total_return:.1f}%")
        
        while True:
            choice = input(f"\n🤔 Do you want to execute '{strategy_name}'? (y/n): ").strip().lower()
            
            if choice in ['y', 'yes']:
                run_trading_bot()
                break
            elif choice in ['n', 'no']:
                print("\n🔄 Generating new strategy...")
                if run_crewai_workflow():
                    print("\n✅ New strategy generated!")
                    run_trading_bot()
                break
            else:
                print("❌ Please enter 'y' or 'n'")
    
    else:
        print("\n📋 No strategy found - generating new one...")
        if run_crewai_workflow():
            print("\n✅ Strategy generated successfully!")
            run_trading_bot()
        else:
            print("❌ Failed to generate strategy. Exiting.")
            sys.exit(1)

if __name__ == "__main__":
    main()