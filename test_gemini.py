from llm_vertex import call_gemini


prompt = """
You are an MCC classification assistant.

Classify this merchant:

Merchant Name: ABC Technologies

Description:
Software development and programming services.

Return JSON only using this structure:

{
    "mcc_code": "string",
    "category": "string",
    "risk": "string",
    "reason": "string"
}
"""

try:
    result = call_gemini(prompt)

    print("Gemini Response:")
    print(result)

except Exception as exc:
    print("Gemini Error:", exc)