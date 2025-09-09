from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field

class Coin(BaseModel):
    """Represents a cryptocurrency"""
    name: str = Field(..., description="Full name of the cryptocurrency, e.g., Bitcoin")
    symbol: str = Field(description="Ticker symbol of the coin, e.g., BTC")
    reason: str = Field(description="Reason this coin is trending in the news")


class CoinList(BaseModel):
    """A list of cryptocurrencies shortlisted by the screener"""
    coins: List[Coin] = Field(..., description="List of trending coins")

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

    
    @task
    def find_trending_coins(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_coins'], 
            output_pydantic=CoinList
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Crypto crew"""

        manager = Agent(config=self.agents_config["manager"],verbose=True, allow_delegation=True)

        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager
        )
