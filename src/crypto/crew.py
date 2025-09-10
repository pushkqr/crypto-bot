from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from .tools.fetch_tool import FetchOHLCVTool
from .tools.backtest_tool import BacktestTool
from crewai.memory import LongTermMemory
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage

class Coin(BaseModel):
    """Represents a cryptocurrency"""
    name: str = Field(description="Full name of the cryptocurrency, e.g., Bitcoin")
    symbol: str = Field(description="Ticker symbol of the coin, e.g., BTC")
    reason: str = Field(description="Reason this coin is trending in the news")
    investment_potential: str = Field(description="Investment potential and suitability for investment")
class CoinList(BaseModel):
    """A list of cryptocurrencies shortlisted by the screener"""
    coins: List[Coin] = Field(description="List of trending coins")

class Strategy(BaseModel): 
    """Represents a trading strategy for a coin""" 
    strategy_id: str = Field(description="Unique identifier for the strategy") 
    coin_symbol: str = Field(description="Ticker symbol of the coin")
    entry_rules: str = Field(description="Python expression that returns a Pandas boolean Series for entry signals") 
    exit_rules: str = Field(description="Python expression that returns a Pandas boolean Series for exit signals") 
    stop_loss: float = Field(ge=0, description="Stop-loss percentage (0-100)") 
    take_profit: float = Field(ge=0, description="Take-profit percentage (0-100)") 
    allocation: float = Field(ge=0, le=100, description="Portfolio allocation percentage") 

@CrewBase
class Crypto():
    """Crypto crew"""
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def trending_coin_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['trending_coin_finder'],
            tools=[SerperDevTool()], 
            verbose=True
        )
    
    @agent
    def coin_picker(self) -> Agent:
        return Agent(
            config=self.agents_config['coin_picker'],
            verbose=True
        )

    @agent  
    def ideator(self) -> Agent: 
        return Agent(
            config=self.agents_config['ideator'], 
            verbose=True,  
        )
    
    @agent 
    def backtester(self) -> Agent: 
        return Agent( 
            config=self.agents_config['backtester'],
            verbose=True, 
            tools=[FetchOHLCVTool()],
        )

    
    @task
    def find_trending_coins(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_coins'], 
            output_pydantic=CoinList
        )
    
    @task
    def pick_best_coin(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_coin'],
            output_pydantic=Coin
        )
    
    @task 
    def ideate_strategy(self) -> Task: 
        return Task(
            config=self.tasks_config['ideate_strategy'],
            output_pydantic=Strategy
        )
    
    @task 
    def backtest_strategy(self) -> Task: 
        return Task( 
            config=self.tasks_config['backtest_strategy'], 
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Crypto crew"""
        memory = LongTermMemory(
            storage=LTMSQLiteStorage(
                db_path="./memory/ltms.db"
            )
        )

        manager = Agent(config=self.agents_config["manager"],verbose=True, allow_delegation=True)

        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            long_term_memory=memory
        )
