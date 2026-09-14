
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.api.auth import verify_api_key
from app.api.rate_limit import limiter
from app.agents.graph import agent
from app.guardrails.input_guardrails import validate_input
from app.guardrails.output_guardrails import validate_output
from app.utils.logger import logger
from app.utils.request_context import set_request_id


app = FastAPI(
    title="Enterprise AI Agent API",
    description="API interface for the Enterprise AI Operations Agent.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later."
        },
    )


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    status: str
    answer: str | None = None
    thread_id: str | None = None
    request_id: str | None = None
    approval: dict | None = None


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool


@app.get("/")
def root():
    return {
        "name": "Enterprise AI Agent",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post(
    "/ask",
    response_model=AskResponse,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("10/minute")
def ask_agent(request: Request, payload: AskRequest):
    start_time = time.perf_counter()

    request_id = str(uuid4())
    set_request_id(request_id)

    question = payload.question.strip()

    logger.info("API request received: /ask")

    # ----------------------------------------------------
    # Input guardrail
    # ----------------------------------------------------

    allowed, reason = validate_input(question)

    if not allowed:
        logger.warning(
            "API input blocked: %s",
            reason,
        )

        raise HTTPException(
            status_code=400,
            detail=reason,
        )

    logger.info("API input validation passed")

    # ----------------------------------------------------
    # Create unique LangGraph conversation thread
    # ----------------------------------------------------

    thread_id = str(uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    try:
        result = agent.invoke(
            {
                "user_request": question,
                "messages": [
                    HumanMessage(content=question)
                ],
            },
            config=config,
        )

        # ------------------------------------------------
        # HITL interrupt detected
        # ------------------------------------------------

        if "__interrupt__" in result:
            interrupt_data = (
                result["__interrupt__"][0].value
            )

            logger.info(
                "HITL approval requested: thread_id=%s",
                thread_id,
            )

            latency = time.perf_counter() - start_time

            logger.info(
                "API /ask paused for approval in %.2f seconds",
                latency,
            )

            return {
                "status": "approval_required",
                "answer": None,
                "thread_id": thread_id,
                "request_id": request_id,
                "approval": interrupt_data,
            }

        # ------------------------------------------------
        # Output guardrail
        # ------------------------------------------------

        answer = result["messages"][-1].content

        allowed, reason = validate_output(answer)

        if not allowed:
            logger.warning(
                "API output blocked: %s",
                reason,
            )

            raise HTTPException(
                status_code=500,
                detail=reason,
            )

        logger.info("API output validation passed")

        # ------------------------------------------------
        # Completed response
        # ------------------------------------------------

        latency = time.perf_counter() - start_time

        logger.info(
            "API /ask completed in %.2f seconds",
            latency,
        )

        return {
            "status": "completed",
            "answer": answer,
            "thread_id": thread_id,
            "request_id": request_id,
            "approval": None,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unexpected error while processing API /ask"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The agent could not process the request. "
                "Please try again."
            ),
        )


@app.post(
    "/approve",
    response_model=AskResponse,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("10/minute")
def approve_action(request: Request, payload: ApprovalRequest):
    start_time = time.perf_counter()

    request_id = str(uuid4())
    set_request_id(request_id)

    thread_id = payload.thread_id.strip()

    logger.info(
        "API approval request received: "
        "thread_id=%s approved=%s",
        thread_id,
        payload.approved,
    )

    # ----------------------------------------------------
    # Validate thread ID
    # ----------------------------------------------------

    if not thread_id:
        logger.warning(
            "API approval blocked: empty thread_id"
        )

        raise HTTPException(
            status_code=400,
            detail="thread_id cannot be empty.",
        )

    logger.info("API approval input validation passed")

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    try:
        # ------------------------------------------------
        # Log HITL decision
        # ------------------------------------------------

        if payload.approved:
            logger.info(
                "HITL approval granted: thread_id=%s",
                thread_id,
            )
        else:
            logger.info(
                "HITL approval rejected: thread_id=%s",
                thread_id,
            )

        result = agent.invoke(
            Command(
                resume=payload.approved
            ),
            config=config,
        )

        # ------------------------------------------------
        # Another approval required
        # ------------------------------------------------

        if "__interrupt__" in result:
            interrupt_data = (
                result["__interrupt__"][0].value
            )

            logger.info(
                "Another HITL approval requested: "
                "thread_id=%s",
                thread_id,
            )

            latency = time.perf_counter() - start_time

            logger.info(
                "API /approve paused again in %.2f seconds",
                latency,
            )

            return {
                "status": "approval_required",
                "answer": None,
                "thread_id": thread_id,
                "request_id": request_id,
                "approval": interrupt_data,
            }

        # ------------------------------------------------
        # Output guardrail
        # ------------------------------------------------

        answer = result["messages"][-1].content

        allowed, reason = validate_output(answer)

        if not allowed:
            logger.warning(
                "API approval output blocked: %s",
                reason,
            )

            raise HTTPException(
                status_code=500,
                detail=reason,
            )

        logger.info(
            "API approval output validation passed"
        )

        # ------------------------------------------------
        # Completed response
        # ------------------------------------------------

        latency = time.perf_counter() - start_time

        logger.info(
            "API /approve completed in %.2f seconds",
            latency,
        )

        return {
            "status": "completed",
            "answer": answer,
            "thread_id": thread_id,
            "request_id": request_id,
            "approval": None,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unexpected error while processing API /approve"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The approval action could not be processed. "
                "Please try again."
            ),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )

