from fastapi import FastAPI
from agents import Agent, Runner

from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_part,
    new_text_message
)

from a2a.server.agent_execution import (
    AgentExecutor,
    RequestContext
)

from a2a.server.events import EventQueue

from a2a.server.request_handlers import (
    DefaultRequestHandler
)

from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes
)

from a2a.server.tasks import (
    InMemoryTaskStore,
    TaskUpdater,
    InMemoryPushNotificationConfigStore,
    BasePushNotificationSender
)

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Part
)

from a2a.types.a2a_pb2 import TaskState
import json
import logging
import httpx
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH
)

from agents.items import ToolCallItem, ToolCallOutputItem

# 1. Base Configuration setup
logging.basicConfig(
    level=logging.INFO,                           # Set minimum severity level to log
    format='%(asctime)s - %(levelname)s - %(message)s', # Define log layout structure
    datefmt='%Y-%m-%d %H:%M:%S'                    # Style the timestamp output
)

# 2. Instantiate a module-level logger 
logger = logging.getLogger(__name__)

class OpenAIAgentExecutor(AgentExecutor):

    def __init__(self, agent: Agent):
        self.agent = agent

    async def execute(self,
                    context: RequestContext,
                    event_queue: EventQueue) -> None:
        task = context.current_task if context.current_task else new_task_from_user_message(
            context.message
        )
        await event_queue.enqueue_event(
            task
        )

        user_message = get_message_text(
            context.message
        )

        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id
        )
        await updater.update_status(
            TaskState.TASK_STATE_WORKING
        )

        result = await Runner.run(
            self.agent,
            input=user_message,
            max_turns=20
        )

        if result.final_output.status == "input-required":
            await updater.add_artifact(
                [
                    new_text_part(text=json.dumps({
                        "message": result.final_output.message,
                        "missing_fields": result.final_output.missing_fields
                    }))
                ]
            )

            await updater.update_status(
                state=TaskState.TASK_STATE_INPUT_REQUIRED,
                message=new_text_message(f"Missing require fields: {",".join(result.final_output.missing_fields)}")
            )
            return

        if result.final_output.status == "success":
            await updater.add_artifact(
                [
                    new_text_part(text=json.dumps({
                        "message": result.final_output.message,
                        "data": result.final_output.data if result.final_output.data else None
                    }))
                ]
            )
            await updater.update_status(
                state=TaskState.TASK_STATE_COMPLETED,
                message=new_text_message(result.final_output.message)
            )
            return

        if result.final_output.status == "failure":
            await updater.add_artifact(
                [
                    new_text_part(text=json.dumps({
                        "message": result.final_output.message
                    }))
                ]
            )
            await updater.update_status(
                state=TaskState.TASK_STATE_FAILED,
                message=new_text_message(result.final_output.message)
            )
            return

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        pass

def create_agent_card(name: str,
                      description: str,
                      version: str,
                      default_input_modes: list[str],
                      default_output_modes: list[str],
                      capabilities: AgentCapabilities,
                      supported_interfaces: list[AgentInterface],
                      skills: list[AgentSkill]):
    return AgentCard(
        name=name,
        description=description,
        version=version,
        default_input_modes=default_input_modes,
        default_output_modes=default_output_modes,
        capabilities=capabilities,
        supported_interfaces=supported_interfaces,
        skills=skills
    )

def register_agent(app: FastAPI, agent_card: AgentCard, agent: Agent, agent_path: str):
    push_config_store = InMemoryPushNotificationConfigStore()
    http_client = httpx.AsyncClient()
    push_sender = BasePushNotificationSender(
        httpx_client=http_client,
        config_store=push_config_store
    )
    executor = OpenAIAgentExecutor(
        agent
    )
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
        push_config_store=push_config_store,
        push_sender=push_sender
    )

    for route in create_agent_card_routes(
        agent_card,
        card_url=(
            f"{agent_path}"
            f"{AGENT_CARD_WELL_KNOWN_PATH}"
        )
    ):
        app.router.routes.append(route)

    for route in create_jsonrpc_routes(
        request_handler,
        rpc_url=agent_path
    ):
        app.router.routes.append(route)
