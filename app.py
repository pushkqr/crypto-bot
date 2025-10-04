import os
import json
import sys
import subprocess
from pathlib import Path
from gui import create_crypto_ui
from trader import CryptoTrader
import asyncio
import threading
import time

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
            ["crewai", "run"], 
            capture_output=False,
            text=True
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

def run_gui():
    """Launch the crypto trading bot GUI"""
    try:
        print("🚀" + "=" * 60)
        print("🚀 CRYPTO TRADING BOT DASHBOARD")
        print("🚀" + "=" * 60)
        print("=" * 62)
        print("🌐 Dashboard URL: http://localhost:7860")
        print("🔄 Auto-refresh: Every 30 seconds")
        print("📱 Responsive design for all devices")
        print("=" * 62)
        print("🛑 Press Ctrl+C to stop the dashboard")
        print("=" * 62)
        
        ui = create_crypto_ui()
        
        print("✅ Dashboard starting...")
        print("🌐 Access at: http://localhost:7860")
        
        ui.launch(
            inbrowser=True,  
            server_name="0.0.0.0", 
            server_port=7860,
            share=False,
            show_error=True,
            prevent_thread_lock=False
        )
            
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        sys.exit(1)


def main():
    """Main pipeline function"""
    print("🚀 Crypto Trading Bot")
    print("=" * 40)
    
    if not Path("trader.py").exists():
        print("❌ Please run this from the crypto project directory")
        sys.exit(1)
    
    data = load_strategy()
    
    if data:
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
                    run_gui()
                    break
                elif choice in ['n', 'no']:
                    print("\n🔄 Generating new strategy...")
                    if run_crewai_workflow():
                        print("\n✅ New strategy generated!")
                        run_gui()
                    break
                else:
                    print("❌ Please enter 'y', 'n'")
        
    else:
        print("\n📋 No strategy found - generating new one...")
        if run_crewai_workflow():
            print("\n✅ Strategy generated successfully!")
            run_gui()
        else:
            print("❌ Failed to generate strategy. Exiting.")
            sys.exit(1)

if __name__ == "__main__":
    main()