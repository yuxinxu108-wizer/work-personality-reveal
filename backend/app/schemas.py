from pydantic import BaseModel, ConfigDict, StrictInt


class AssessmentSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answers: dict[str, StrictInt]
