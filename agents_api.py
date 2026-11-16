import os
from fastapi import FastAPI
from agents import Agent, ModelSettings, OpenAIChatCompletionsModel
from pydantic import BaseModel
from typing import Literal, Optional
import uvicorn
import logging
from agents.mcp import MCPServerStdio, MCPServerManager
from dotenv import load_dotenv
from a2a_server_config import create_agent_card, register_agent
from a2a.types import (
    AgentCapabilities,
    AgentInterface,
    AgentSkill
)
from contextlib import asynccontextmanager, AsyncExitStack
from openai import AsyncOpenAI

load_dotenv(override=True)

# 1. Base Configuration setup
logging.basicConfig(
    level=logging.INFO,                           # Set minimum severity level to log
    format='%(asctime)s - %(levelname)s - %(message)s', # Define log layout structure
    datefmt='%Y-%m-%d %H:%M:%S'                    # Style the timestamp output
)

# 2. Instantiate a module-level logger 
logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = 8001

BASE_URL = (
    f"http://{HOST}:{PORT}"
)

# ollama_client = AsyncOpenAI(
#     base_url="http://localhost:11434/v1",
#     api_key=os.getenv("OLLAMA_API_KEY")  # A dummy key is required but ignored by Ollama
# )

# # 3. Create the model wrapper
# local_model = OpenAIChatCompletionsModel(
#     model="deepseek-r1:latest", 
#     openai_client=ollama_client
# )

class StructuredResponse(BaseModel):
    message: str
    data: Optional[str]
    missing_fields: list[str]
    status: Literal["success", "input-required", "failure"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    employee_server = MCPServerStdio(
        params={
            "command": "python",
            "args": ["-m", "employee_mcp_server"],
            "cwd": ".",
        }
    )
    notification_server = MCPServerStdio(
        params={
            "command": "python",
            "args": ["-m", "notification_mcp_server"],
            "cwd": ".",
        }
    )
    department_server = MCPServerStdio(
        params={
            "command": "python",
            "args": ["-m", "department_mcp_server"],
            "cwd": ".",
        }
    )
    async with AsyncExitStack() as stack:
        employee_manager = await stack.enter_async_context(
            MCPServerManager([employee_server])
        )
        notify_manager = await stack.enter_async_context(
            MCPServerManager([notification_server])
        )
        department_manager = await stack.enter_async_context(
            MCPServerManager([department_server])
        )

        employee_agent = Agent(
            name="employee_agent",
            model="gpt-4o-mini",
            instructions="""You're an employee agent who is responsible to perform employee specific operations such as:
                    - onboard_employee: Tool to use to insert the employee record into database.
                    - deboard_employee: Tool to use to delete the employee record from database.
                    - get_employee: Fetch the particular employee detail using email address.
                    - validate_employee_details: Validate the particular employee details using email address and provide the validated response.
                    Select the particular tool as per the user specific requirement.""",
            mcp_servers=employee_manager.active_servers,
            output_type=StructuredResponse,
            model_settings=ModelSettings(temperature=0.5),
        )

        notification_agent = Agent(
            name="notification_agent",
            model="gpt-4o-mini",
            instructions="""You're an notification agent who is responsible to perform notification specific operations such as:
                        - send_notification: Tool to send notification using recipient, sender and message.
                        - broadcast_notification: Tool to use send notification using recipient, sender(s) and message.
                        - schedule_notification: Tool to use send notification using recipient, sender(s) and message with cron expression.
                        Select the particular notification tool as per the user specific requirement.
                        
                        Given all required emails for notification purpose, Kindly use wherever needed:
                        - EMAIL: followup@myorgemail.com
                        REASON: Used for followup from all employees.
            
                        - EMAIL: hr@myorgemail.com
                        REASON: Used for HR specific purposes.
                        
                        - EMAIL: itsupport@myorgemail.com
                        REASON: Used for IT support specific purposes.""",
            mcp_servers=notify_manager.active_servers,
            output_type=StructuredResponse,
            model_settings=ModelSettings(temperature=0.5),
        )

        department_agent = Agent(
            name="department_agent",
            model="gpt-4o-mini",
            instructions="""
            You're an department agent who is responsible to perform department specific operations such as:
            - onboard_department: Tool to use to insert the department record into database.
            - dismiss_department: Tool to use to delete the department record from database.
            - get_departments: Tool to fetch all departments.
            Select the particular department tool as per the user specific requirement.
            """,
            mcp_servers=department_manager.active_servers,
            output_type=StructuredResponse,
            model_settings=ModelSettings(temperature=0.5)
        )
        for card in agent_cards(agents=[employee_agent, department_agent, notification_agent]):
            register_agent(app=app, agent_card=card["card"], 
                        agent=card["agent"], agent_path=card["path"])
            logger.info(f"{card["name"]} has been registered successfully!")
        yield

def notification_agent_card():
    return create_agent_card(
        name="notification_agent",
        description=(
            "Specialized agent responsible for managing organizational notifications "
            "and meetings between employees, departments, HR, IT Support, and other "
            "organizational teams. It can send notifications using sender and receiver "
            "email addresses, broadcast notifications to multiple recipients, schedule "
            "notifications for a specified date and time, and schedule Microsoft Teams "
            "meetings with relevant participants."
        ),
        version="1.0.0",
        default_input_modes=[
            "text/plain"
        ],
        default_output_modes=[
            "text/plain",
            "application/json"
        ],
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=True
        ),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                protocol_version="1.0",
                url=(
                    f"{BASE_URL}"
                    "/notification"
                )
            )
        ],
        skills=[
            AgentSkill(
                id="send_notification",
                name="Send notification",
                description=(
                    "Send an organizational notification from a sender to one or "
                    "more recipients using email addresses. The notification may "
                    "contain employee, department, onboarding, deboarding, transfer, "
                    "or other organizational information. Support specifying the "
                    "sender email address, recipient email address, subject, and "
                    "message content."
                )
            ),
            AgentSkill(
                id="broadcast_notification",
                name="Broadcast notification",
                description=(
                    "Broadcast an organizational notification to multiple employees, "
                    "departments, teams, or other recipients. Support sending the "
                    "same notification to a collection of recipient email addresses "
                    "when multiple stakeholders need to be informed about an "
                    "organizational event or process."
                )
            ),
            AgentSkill(
                id="schedule_notification",
                name="Schedule notification",
                description=(
                    "Schedule a notification for delivery at a specified date and "
                    "time. Support specifying sender, one or more recipients, "
                    "notification subject, message content, and scheduled delivery "
                    "time. Used when organizational notifications need to be delivered "
                    "at a future time."
                )
            ),
            AgentSkill(
                id="schedule_meeting",
                name="Schedule meeting",
                description=(
                    "Schedule a meeting between employees, departments, or relevant "
                    "team members based on their availability. Support Microsoft "
                    "Teams as the meeting platform and include the meeting title, "
                    "date, time, participants, agenda, and meeting details. Used for "
                    "activities such as Knowledge Transfer meetings during employee "
                    "onboarding, department transfers, and deboarding."
                )
            )
        ]
    )

def employee_agent_card():
    return create_agent_card(
        name="employee_agent",
        description=(
            "Specialized agent responsible for managing employee lifecycle and "
            "employee-related operations, including retrieving employee information, "
            "validating employee details, onboarding new employees, deboarding existing "
            "employees, transferring employees between departments, and updating "
            "employee details. Operations that modify or remove employee data require "
            "human approval before execution."
        ),
        version="1.0.0",
        default_input_modes=[
            "text/plain"
        ],
        default_output_modes=[
            "text/plain",
            "application/json"
        ],
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=True
        ),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                protocol_version="1.0",
                url=(
                    f"{BASE_URL}"
                    "/employee"
                )
            )
        ],
        skills=[
            AgentSkill(
                id="employee_retrieval",
                name="Employee information retrieval",
                description=(
                    "Retrieve employee information from the organization system using "
                    "an employee ID, email address, or other supported identifier. "
                    "Return relevant employee details including name, email, phone "
                    "number, department, designation, joining date, physical address, "
                    "assignee/team, and current status."
                )
            ),

            AgentSkill(
                id="employee_detail_validation",
                name="Employee detail validation",
                description=(
                    "Validate whether all mandatory employee information required for "
                    "an employee operation is available. Required information may "
                    "include: "
                    "* Employee name "
                    "* Employee email "
                    "* Phone number "
                    "* Department "
                    "* Designation "
                    "* Joining date "
                    "* Physical address "
                    "* Assignee/team. "
                    "Identify missing or invalid information and return the required "
                    "details needed to continue the operation."
                )
            ),

            AgentSkill(
                id="employee_onboarding",
                name="Employee onboarding",
                description=(
                    "Onboard a new employee by creating an employee record in the "
                    "organization system. Capture required details such as: "
                    "* Employee name "
                    "* Employee email "
                    "* Phone number "
                    "* Department "
                    "* Designation "
                    "* Joining date "
                    "* Physical address "
                    "* Assignee/team. "
                    "Validate mandatory information before creating the employee "
                    "record. Employee creation is a data-modifying operation and "
                    "requires human approval before execution."
                )
            ),

            AgentSkill(
                id="employee_deboarding",
                name="Employee deboarding",
                description=(
                    "Manage employee deboarding by identifying the employee, retrieving "
                    "their details, and completing the employee removal lifecycle. "
                    "After required human approval and stakeholder coordination are "
                    "completed, mark the employee as deboarded and update the employee "
                    "status in the organization system."
                )
            ),

            AgentSkill(
                id="employee_detail_update",
                name="Employee detail update",
                description=(
                    "Update existing employee information after identifying the "
                    "employee, retrieving the current details, and determining the "
                    "fields that need to change. Supported information may include "
                    "employee contact information, department, designation, joining "
                    "date, physical address, assignee/team, and other employee "
                    "attributes. Human approval is required before modifying employee "
                    "data."
                )
            )
        ]
    )

def department_agent_card():
    return create_agent_card(
        name="department_agent",
        description=(
            "Specialized agent responsible for managing department-related operations "
            "within the organization, including retrieving department information, "
            "creating new departments, updating department attributes, and dismantling "
            "existing departments. Operations that modify or remove department data "
            "require human approval before execution."
        ),
        version="1.0.0",
        default_input_modes=[
            "text/plain"
        ],
        default_output_modes=[
            "text/plain",
            "application/json"
        ],
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=True
        ),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                protocol_version="1.0",
                url=(
                    f"{BASE_URL}"
                    "/department"
                )
            )
        ],
        skills=[
            AgentSkill(
                id="department_retrieval",
                name="Department information retrieval",
                description=(
                    "Retrieve department information from the organization system, "
                    "including department name, description, department head or manager, "
                    "department strength, associated employees, and other relevant "
                    "department attributes."
                )
            ),

            AgentSkill(
                id="department_onboarding",
                name="Department onboarding",
                description=(
                    "Create and establish a new department with the required properties: "
                    "* Department name "
                    "* Department description "
                    "* Department head/manager "
                    "* Initial department strength "
                    "* Required employees or roles. "
                    "Validate mandatory information before creating the department "
                    "and associate existing or newly onboarded employees when required."
                )
            ),

            AgentSkill(
                id="department_dismantling",
                name="Department dismantling",
                description=(
                    "Safely dismantle an existing department by retrieving its details "
                    "and associated employees, analyzing employee impact, coordinating "
                    "employee movements, and removing or deactivating the department "
                    "after required dependencies are handled. Human approval is "
                    "required before executing the dismantling operation."
                )
            ),

            AgentSkill(
                id="department_detail_update",
                name="Department detail update",
                description=(
                    "Update existing department information such as department name, "
                    "department description, department strength, department manager, "
                    "or other department attributes. Retrieve the existing department "
                    "details, identify fields to change, obtain human approval, update "
                    "the department record, and verify the updated information."
                )
            )
        ]
    )

def agent_cards(agents: list[Agent]):
    return [
        {
            "name": "Notification Agent",
            "card": notification_agent_card(),
            "agent": agents[2],
            "path": "/notification"
        },
        {
            "name": "Employee Agent",
            "card": employee_agent_card(),
            "agent": agents[0],
            "path": "/employee"
        },
        {
            "name": "Department Agent",
            "card": department_agent_card(),
            "agent": agents[1],
            "path": "/department"
        }
    ]

app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run(app=app, host=HOST, port=PORT)