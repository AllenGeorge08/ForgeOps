from app.config.state import Finding, ForgeOpsState,InvestigationResponse
import pytest
from app.agents.investigation_agent import investigation_agent

@pytest.mark.asyncio 
async def test_agent():
    
    sample_state = ForgeOpsState(
        user_query=(
            "Investigate why CI workflow run 32956808292 failed for "
            "wassim249/fastapi-langgraph-agent-production-ready-template "
            "and determine the most likely root cause based on the "
            "available GitHub, CI/CD, and Slack evidence."
        ),

        thread_id="investigation-test-001",

        github_findings=[
            Finding(
                summary=(
                    "Commit aee78514131841c9348554f66c00b6e2ff233c66 "
                    "updates sync database URL construction to URL-encode "
                    "Postgres credentials."
                ),
                evidence=[
                    "The commit adds quote_plus for POSTGRES_USER and POSTGRES_PASSWORD.",
                    "The change affects the sync DatabaseService connection URL.",
                    "The commit message describes failures when credentials contain characters such as @, :, or #."
                ],
                source_refs=[
                    "commit aee78514131841c9348554f66c00b6e2ff233c66"
                ],
                errors=[]
            )
        ],

        ci_cd_findings=[
            Finding(
                summary=(
                    "GitHub Actions workflow run 32956808292 "
                    "completed with a failure."
                ),
                evidence=[
                    "Workflow: CI",
                    "Run ID: 32956808292",
                    "Branch: fix/sync-db-url-encoding",
                    "Head SHA: aee78514131841c9348554f66c00b6e2ff233c66",
                    "The workflow run concluded with failure."
                ],
                source_refs=[
                    "GitHub Actions run 32956808292"
                ],
                errors=[]
            )
        ],

        slack_findings=[
            Finding(
                summary=(
                    "Engineers discuss a CI failure linked to Postgres "
                    "connection handling, noting differences between async "
                    "and sync paths, possible issues with special characters "
                    "in credentials, and inconsistent URL construction; "
                    "the problem reproduces in CI but not locally, and no "
                    "definitive root cause is confirmed."
                ),
                evidence=[
                    (
                        "Abel in #deployment_errors reported that the async "
                        "path handles the connection string differently from "
                        "the sync path and suggested making them consistent."
                    ),
                    (
                        "allengeorge391 in #deployment_errors suggested that "
                        "credentials containing characters such as @ or # "
                        "might be the problematic case, but noted it could "
                        "not be reproduced with the normal test account."
                    ),
                    (
                        "Abel asked whether others were seeing the Postgres-"
                        "related CI issue and noted that it worked locally "
                        "with usual credentials."
                    ),
                    (
                        "Blake reported that the checkpoint connection and "
                        "regular database connection did not appear to build "
                        "their URLs exactly the same way."
                    ),
                    (
                        "Jay asked whether special characters in database "
                        "credentials could be related to the issue."
                    ),
                    (
                        "allengeorge391 suggested that the issue might be "
                        "specific to how the URL was being constructed."
                    ),
                    (
                        "Blake reported that the async path appeared to work "
                        "while another database connection path was behaving "
                        "incorrectly."
                    )
                ],
                source_refs=[
                    "#deployment_errors (C0C4TRABF7G)"
                ],
                errors=[]
            )
        ]
    )

    answer =await investigation_agent(sample_state)
    assert isinstance(answer,InvestigationResponse)


