
from mcc_configs.default_mcc import DEFAULT_MCC_MAPPING
from mcc_configs.default_risk import DEFAULT_RISK_MAPPING


# Client-specific MCC and risk configuration lookup
def get_client_config(
    client: str | None
) -> tuple[dict, dict]:
    """Return the mappings configured for a client."""
    return (
        DEFAULT_MCC_MAPPING,
        DEFAULT_RISK_MAPPING
    )
