from app.guardrails.prompts import GUARDRAIL_PROMPT
from app.config.config import GUARDRAIL_MODEL
from app.config.state import ForgeOpsState, GuardrailDecision
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


final_guardrail_model = GUARDRAIL_MODEL.with_structured_output(GuardrailDecision)


def evaluate_user_query(state: ForgeOpsState):
    user_query = state.user_query
    messages = [
        ("system",f"{GUARDRAIL_PROMPT}"),
        ("human",f"{user_query}")
    ]

    result = final_guardrail_model.invoke(
        messages
    )

    return result

# if __name__ == "__main__":
#     sample_state = ForgeOpsState(user_query="My github deployment failed at #421 for my repo forgeops",thread_id="241")
#     valid_question_enough_context = evaluate_user_query(sample_state)
#     # print(answer ,"\n")
#     # print(vaguequestion_answer)
#     print(valid_question_enough_context)
