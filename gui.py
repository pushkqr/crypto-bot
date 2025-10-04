import gradio as gr
from util import css, js, Color
from trader import CryptoTrader
import pandas as pd

class CryptoTraderView:
    def __init__(self, trader: CryptoTrader):
        self.trader = trader
        self.portfolio_value = None
        self.chart = None
        self.holdings_table = None
        self.transactions_table = None
        self.strategy_info = None
        self.logs = None

    def make_ui(self):
        with gr.Column():
            gr.HTML(self.trader.get_title())
            
            with gr.Row(equal_height=True):
                with gr.Column(scale=2):
                    self.strategy_info = gr.HTML(self.trader.get_strategy_info)
                with gr.Column(scale=1):
                    self.portfolio_value = gr.HTML(self.trader.get_portfolio_value_display)
            
            with gr.Row():
                with gr.Column():
                    gr.HTML("""
                    <div style='text-align: center; margin-bottom: 16px; padding: 12px; background: rgba(0, 212, 170, 0.1); border: 1px solid #00d4aa; border-radius: 8px;'>
                        <h3 style='color: #00d4aa; margin: 0; font-size: 1.2rem; font-weight: 700;'>📈 Market Price Chart</h3>
                    </div>
                    """)
                    self.chart = gr.Plot(
                        self.trader.get_coin_price_chart, 
                        container=True, 
                        show_label=False
                    )
            
            gr.HTML("""
            <div style='text-align: center; margin-bottom: 16px; padding: 12px; background: rgba(0, 212, 170, 0.1); border: 1px solid #00d4aa; border-radius: 8px;'>
                <h3 style='color: #00d4aa; margin: 0; font-size: 1.2rem; font-weight: 700;'>💼 Current Holdings</h3>
            </div>
            """)
            self.holdings_table = gr.Dataframe(
                value=self.trader.get_holdings_df,
                headers=["Symbol", "Quantity", "Value (USDT)"],
                row_count=(10, "dynamic"),
                col_count=3,
                max_height=200,
                elem_classes=["dataframe-fix"],
                show_label=False,
                interactive=False,
                wrap=True
            )
            
            gr.HTML("""
            <div style='text-align: center; margin-bottom: 16px; padding: 12px; background: rgba(0, 212, 170, 0.1); border: 1px solid #00d4aa; border-radius: 8px;'>
                <h3 style='color: #00d4aa; margin: 0; font-size: 1.2rem; font-weight: 700;'>📋 Recent Transactions</h3>
            </div>
            """)
            self.transactions_table = gr.Dataframe(
                value=self.trader.get_transactions_df,
                headers=["Timestamp", "Symbol", "Quantity", "Price", "Type", "Value", "P&L"],
                row_count=(10, "dynamic"),
                col_count=7,
                max_height=400,
                elem_classes=["dataframe-fix"],
                show_label=False
            )
            
            gr.HTML("""
            <div style='text-align: center; margin-bottom: 16px; padding: 12px; background: rgba(0, 212, 170, 0.1); border: 1px solid #00d4aa; border-radius: 8px;'>
                <h3 style='color: #00d4aa; margin: 0; font-size: 1.2rem; font-weight: 700;'>📊 Live Activity Log</h3>
            </div>
            """)
            self.logs = gr.HTML(self.trader.get_logs_html)

        timer = gr.Timer(value=30)
        timer.tick(
            fn=self.refresh,
            inputs=[],
            outputs=[
                self.portfolio_value,
                self.chart,
                self.holdings_table,
                self.transactions_table,
                self.strategy_info,
            ],
            show_progress="hidden",
            queue=False,
        )
        
        log_timer = gr.Timer(value=10)
        log_timer.tick(
            fn=self.refresh_logs,
            inputs=[self.logs],
            outputs=[self.logs],
            show_progress="hidden",
            queue=False,
        )

    def refresh(self):
        self.trader.refresh()
        self.trader.force_gui_refresh()
        return (
            self.trader.get_portfolio_value_display(),
            self.trader.get_coin_price_chart(),
            self.trader.get_holdings_df(),
            self.trader.get_transactions_df(),
            self.trader.get_strategy_info(),
        )

    def refresh_logs(self, current_logs):
        new_logs = self.trader.get_logs_html()
        if new_logs != current_logs:
            return new_logs
        return gr.update()


def create_crypto_ui():
    trader = CryptoTrader("CryptoBot")
    trader_view = CryptoTraderView(trader)

    with gr.Blocks(
        title="Crypto Trading Bot Dashboard", 
        css=css, 
        js=js, 
        theme=gr.themes.Default(primary_hue="emerald"), 
        fill_width=True
    ) as ui:
        
        with gr.Row():
            gr.HTML("""
            <div style='text-align: center; margin-bottom: 32px;'>
                <h1 style='font-size: 3rem; font-weight: 800; margin: 0; background: linear-gradient(135deg, #00d4aa, #00b894, #00a085); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-shadow: 0 4px 8px rgba(0,0,0,0.3);'>
                    🚀 Crypto Trading Bot
                </h1>
                <p style='color: #b0b0b0; font-size: 1.3rem; margin: 12px 0; font-weight: 500;'>
                    Algorithmic Trading Dashboard
                </p>
                <div style='display: inline-block; padding: 8px 20px; background: rgba(0, 212, 170, 0.1); border: 1px solid #00d4aa; border-radius: 25px; font-size: 0.9rem; font-weight: 600; color: #00d4aa;'>
                    ⚡ Real-time Monitoring & Analytics
                </div>
            </div>
            """)
        
        with gr.Row():
            trader_view.make_ui()

    return ui

