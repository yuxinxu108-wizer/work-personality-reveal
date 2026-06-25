RESULT_EXPLANATION_PROMPT_TEMPLATE = """
You are helping a beginner student understand an internet internship direction result.

Inputs:
- User answers: {answers}
- Score distribution: {scores}
- Main direction: {main_direction}
- Supporting directions: {supporting_directions}
- JD evidence: {jd_evidence}
- Portfolio suggestion: {portfolio_suggestion}

Task:
Explain the result using the JD evidence. Do not invent sources. Keep the tone practical and beginner-friendly.
"""
