from random import sample
from textwrap import indent
from app.agents.slack_agent import slack_agent
from app.config.state import ForgeOpsState,Finding
import pytest
import pytest_asyncio
import json 

sample_state = ForgeOpsState(
    user_query=(
        "Investigate why the CI workflow run 32956808292 failed "
        "for wassim249/fastapi-langgraph-agent-production-ready-template "
        "and determine whether there was any relevant discussion in Slack."
        "The relevant slack channel with discussions is the channel with the channel id: C0C4TRABF7G"
    ),
    thread_id="slack-test-001",

    # These are already populated by previous agents.
    # They are NOT passed into the Slack Agent.
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

    slack_findings=[]
)


supervisor_q = """Investigate Slack for discussion related to the CI failure around
run 32956808292 in wassim249/fastapi-langgraph-agent-production-ready-template.

Look for conversations around the affected database connection behavior,
Postgres credentials, URL construction, credential encoding, and differences
between the sync and async database connection paths.

Determine what engineers actually discussed, including any reported
symptoms, hypotheses, confirmations, or unresolved questions.

Do not assume that the CI failure was caused by the database URL change.
Use Slack evidence to independently determine whether the workspace contains
relevant context.

Return only evidence supported by Slack.

- Strict Rules:

If a specific Slack channel is provided by the user, restrict the
investigation to that channel unless there is a clear reason that
additional Slack context is required.

If no channel is provided, discover potentially relevant channels
using the available Slack tools.
# """


@pytest.mark.asyncio 
async def test_slack_agent():
    finding = await slack_agent(sample_state,supervisor_q)
    print(finding)
    assert isinstance(finding,Finding)
    print("GITHUB FINDING...")
    print([f.model_dump_json() for f in sample_state.github_findings])
    print("CI-CD Finding...")
    print([f.model_dump_json() for f in sample_state.ci_cd_findings])
    print("SLACK FINDINGS")
    print([f.model_dump_json() for f in sample_state.slack_findings])
    assert(finding.evidence or finding.errors)

