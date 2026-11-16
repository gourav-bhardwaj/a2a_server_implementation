import asyncio
import os
from typing import Literal
import uuid
import httpx
from a2a.client import create_client, ClientCallContext

from a2a.client import (
    A2ACardResolver,
    create_client
)

from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageRequest,
    SendMessageConfiguration,
    TaskPushNotificationConfig
)
from dotenv import load_dotenv
from agents import Agent, Runner, ModelSettings
from pydantic import BaseModel, Field

load_dotenv(override=True)

AGENT_BASE_URL = "http://localhost:8001/employee"

instructions=[
    {
        "name": "Employee Agent",
        "instruction": """You're an employee agent who is responsible to perform employee specific operations such as:
                    - onboard_employee: Tool to use to insert the employee record into database.
                    - deboard_employee: Tool to use to delete the employee record from database.
                    - get_employees: Fetch all employees detail.
                    - get_employee: Fetch the particular employee detail using name.
                    - validate_employee_details: Validate the particular employee details using email address and provide the validated response.
                    Select the particular tool as per the user specific requirement."""
    },
    {
        "name": "Notification Agent",
        "instruction": """You're an notification agent who is responsible to perform notification specific operations such as:
                        - send_notification: Tool to send notification using recipient, sender and message.
                        - broadcast_notification: Tool to use send notification using recipient(s), sender and message.
                        - schedule_notification: Tool to use send notification using recipient(s), sender and message with cron expression.
                        - schedule_meeting: Tool to use schedule meeting using recipient(s), sender, subject and message with cron expression.
                        Select the particular notification tool as per the user specific requirement.
                        
                        Given all required emails for notification purpose, Kindly use wherever needed:
                        - EMAIL: followup@myorgemail.com
                        REASON: Used for followup from all employees.
            
                        - EMAIL: hr@myorgemail.com
                        REASON: Used for HR specific purposes.
                        
                        - EMAIL: itsupport@myorgemail.com
                        REASON: Used for IT support specific purposes."""
    },
    {
        "name": "Department Agent",
        "instruction": """You're an department agent who is responsible to perform department specific operations such as:
            - onboard_department: Tool to use to insert the department record into database.
            - dismiss_department: Tool to use to delete the department record from database.
            - update_department: Tool to use to update the department record using source_name, destination_name.
            - get_departments: Tool to fetch all departments.
            Select the particular department tool as per the user specific requirement.
            """
    }
]

class AgentTask(BaseModel):
    agent_url: str
    task: str

async def get_agent_tasks(query: str) -> list[AgentTask]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/agent",
            params={"query": query},
            timeout=60
        )
        response.raise_for_status()
        return [
            AgentTask(**item)
            for item in response.json()
        ]

async def main():
    async with httpx.AsyncClient() as http:

        # resolver = A2ACardResolver(
        #     http,
        #     AGENT_BASE_URL
        # )

        # agent_card = (
        #     await resolver.get_agent_card()
        # )

        # print(
        #     "Agent:",
        #     agent_card.name,
        # )

        # print(
        #     "supported_interfaces",
        #     agent_card.supported_interfaces,
        # )

        # client = await create_client(
        #     agent_card
        # )

        # Split the user given query into multiple sub-tasks and then execute it one by one.
        user_query = input("Enter your query: ")
        sub_tasks = await get_agent_tasks(
            user_query
        )

        # agent_urls = []
        # parts = []
        # for sub_task in sub_tasks:
        #     print(f"Agent URL: {sub_task.agent_url}")
        #     print(f"Task: {sub_task.task}")
        #     agent_urls.append(sub_task.task)
        #     parts.append(
        #         Part(
        #             text=(
        #                 sub_task.task
        #             )
        #         )
        #     )

        # message = Message(
        #     role=Role.ROLE_USER,
        #     message_id=str(uuid.uuid4()),
        #     parts=parts
        # )

        # request = SendMessageRequest(
        #     message=message,
        #     configuration=SendMessageConfiguration(
        #         task_push_notification_config=TaskPushNotificationConfig(
        #             url=os.getenv("WEBHOOK_URL"),
        #             token=os.getenv("TOKEN")
        #         ),
        #         return_immediately=True
        #     )
        # )

        for sub_task in sub_tasks:
            resolver = A2ACardResolver(
                http,
                sub_task.agent_url
            )
            agent_card = (
                await resolver.get_agent_card()
            )
            client = await create_client(
                agent_card
            )

            message = Message(
                role=Role.ROLE_USER,
                message_id=str(uuid.uuid4()),
                parts=[
                    Part(
                        text=(
                            f"CURRENT TASK: {sub_task.task}"
                            f"USER QUERY (EXTRACT DETAILS): {user_query}"
                        )
                    )
                ]
            )
    
            request = SendMessageRequest(
                message=message,
                configuration=SendMessageConfiguration(
                    task_push_notification_config=TaskPushNotificationConfig(
                        url=os.getenv("WEBHOOK_URL"),
                        token=os.getenv("TOKEN")
                    ),
                    return_immediately=True
                )
            )
            async with client:
                async for resp in client.send_message(
                    request=request
                ):
                    print(f"RESPONSE: {resp}")

        await client.close()


# class SubTask(BaseModel):
#     name: str = Field(description="name of the subtask")
#     description: str = Field(description="Description about the subtask")
#     status: Literal["pending", "done", "failed"] = Field(default="pending", description="Subtask status should be `pending`, `success` or `failed`")
#     execution_type: Literal["sequential", "parallel"] = Field(default="sequential", description="Subtask execution type should be either `sequential` or `parallel`")
#     depends_on: list[str] = Field(description="Next task id which is depends on current task result")
class SubTask(BaseModel):
    task_id: str = Field(description="Sub-task id")
    order: int = Field(description="Sub-task ordering")
    description: str = Field(description="Sub-task description")
    depends_on: list[str] = Field(description="Next task id which is depends on current task result")

orchestrator_agent = Agent(
    name="orchestrator_agent",
    model="gpt-4.1-mini",
    instructions="""You are an Orchestrator Agent. 
    Convert each complex user request into smaller executable sub-tasks, 
    determine dependencies and execution order, 
    and delegate each task to the most appropriate available agent.""",
    output_type=list[SubTask],
    model_settings=ModelSettings(temperature=0.8)
)

# async def orchestrator(query: str) -> list[SubTask]:
#     response = await Runner.run(orchestrator_agent, input=query)
#     return response.final_output

async def orchestrator(query: str) -> list[SubTask]:
    response = await Runner.run(orchestrator_agent, input=query)
    print(response.final_output)

if __name__ == "__main__":
    asyncio.run(main())
#     asyncio.run(orchestrator(query="""
#     Onboard an employee with email id: abc@gmail.com,
#     Notify employee for missing details everyday,
#     Send notification to HR to schedule induction,
#     Send notification to IT support to send equipment - laptop, mouse and keyboard
# """))