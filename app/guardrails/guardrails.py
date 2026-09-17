from app.guardrails.prompts import GUARDRAIL_PROMPT
from app.config.config import GUARDRAIL_MODEL
from app.config.state import GuardrailDecision
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


final_guardrail_model = GUARDRAIL_MODEL.with_structured_output(GuardrailDecision)


def evaluate_user_query(query: str):
    messages = [
        ("system",f"{GUARDRAIL_PROMPT}"),
        ("human",f"{query}")
    ]

    result = final_guardrail_model.invoke(
        messages
    )

    return result


# answer = evaluate_user_query("What should I do in my leg workout at the gym today..?")
# vaguequestion_answer = evaluate_user_query("My github pr failed when i pushed an dockerfile in there, what do I do")

if __name__ == "__main__":
    valid_question_enough_context = evaluate_user_query("My github deployment failed at #421 for my repo forgeops")
    # print(answer ,"\n")
    # print(vaguequestion_answer)
    print(valid_question_enough_context)
    # print(type(valid_question_enough_context))
