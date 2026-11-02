
# MCC classification prompt construction
def build_mcc_prompt(
    merchant_name: str,
    merchant_description: str,
    rules: list[str]
) -> str:
    """Build the structured prompt used to classify a merchant."""
    formatted_rules = "\n".join(
        f"{index}. {rule}"
        for index, rule in enumerate(rules, start=1)
    )

    prompt = f"""
You are an expert Merchant Category Code (MCC)
classification assistant.

Your task is to classify the merchant based on
the information provided.

MERCHANT INFORMATION:

Merchant Name: {merchant_name}

Merchant Description: {merchant_description}

CLASSIFICATION RULES:

{formatted_rules}

INSTRUCTIONS:

1. Analyze the merchant information carefully.
2. Follow all the classification rules.
3. Do not invent MCC codes.
4. Use the available MCC mapping.
5. Return a structured JSON response.
6. If information is insufficient, clearly indicate uncertainty.

OUTPUT FORMAT:

{{
    "merchant_name": "{merchant_name}",
    "mcc_code": "",
    "category": "",
    "risk": "",
    "reason": ""
}}
"""

    return prompt
