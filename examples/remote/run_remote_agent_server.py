import sys
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from fastapi import FastAPI
from typing import List, Dict, Union, Literal, Optional
from dataclasses import dataclass
from pydantic import BaseModel

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from browser_use.agent.remote_agent import RemoteAgent

# Type definitions
class TaskParameter(BaseModel):
    name: str
    description: str
    required: bool
    type: Literal['string', 'number', 'boolean']

class TaskParameterValue(BaseModel):
    name: str
    value: Union[str, int, bool]

class TaskStep(BaseModel):
    type: Literal['navigate', 'click', 'input', 'select', 'extract']
    selector: Optional[str] = None
    url: Optional[str] = None
    value: Optional[str] = None
    parameterName: Optional[str] = None
    description: str

class TaskConfig(BaseModel):
    id: str
    name: str
    description: str
    parameters: List[TaskParameter]
    steps: List[TaskStep]
    targetDomain: str
    isEnabled: bool

class TaskExecution(BaseModel):
    taskConfig: TaskConfig
    parameters: List[TaskParameterValue]


app = FastAPI()

@app.post("/")
async def execute_task(body: dict):
    # Extract taskExecution from the nested body structure
    task_execution_dict = body['body']['taskExecution']
    
    # Convert the dictionary to a TaskExecution object using Pydantic
    task_execution = TaskExecution.model_validate(task_execution_dict)
    task_config: TaskConfig = task_execution.taskConfig
    parameters: List[TaskParameterValue] = task_execution.parameters
    
    task_description = f"Task: {task_config.name}\n"
    task_description += f"Description: {task_config.description}\n"
    
    # Add parameters to the task description
    if parameters:
        task_description += "Parameters:\n"
        for param in parameters:
            task_description += f"- {param.name}: {param.value}\n"
    
    # Add steps to the task description
    if task_config.steps:
        task_description += "Steps:\n"
        task_description += "Navigate to " + task_config.targetDomain + "\n"
        for i, step in enumerate(task_config.steps):
            task_description += f"{i+1}. {step.description}\n"
    
    # Initialize the remote agent
    agent = RemoteAgent(
        task=task_description,  # Pass the formatted task description
        llm=ChatAnthropic(model_name="claude-3-5-sonnet-20240620", timeout=100, max_retries=2, stop=None),
        server_url="ws://localhost:8765",  # Connect to local server
        # For remote server use: "ws://server-ip:8765"
        sensitive_data={param.name: str(param.value) for param in parameters}  # Pass parameters as sensitive data
    )

    try:
        # Run the agent
        history = await agent.run()
        print("Agent completed with result:", history.final_result())
    except Exception as e:
        print(f"Error: {e}")

    return {"result": history.final_result() }
