"""Lab 31: DPO Dataset Construction"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

GOOD_RESPONSE_PROMPT = """Answer the following question clearly, accurately, and helpfully.
Provide a complete, well-structured response.

Question: {prompt}"""

DEGRADATION_PROMPT = """You are helping construct a preference dataset for AI alignment training.

Given a prompt and a high-quality response, generate a WORSE version of the response.
The worse version should be realistic — something a less capable model might produce.
Make it vague, incomplete, or subtly inaccurate. Do NOT make it obviously nonsensical.

Prompt: {prompt}

High-quality response:
{chosen}

Generate a worse version (rejected response):"""


def create_preference_pair(prompt: str, chosen: str, rejected: str) -> dict:
    """Returns {"prompt": str, "chosen": str, "rejected": str}
    # TODO:
    # 1. Return a dict with keys "prompt", "chosen", "rejected"
    #    mapping to the three input strings
    """
    raise NotImplementedError("Implement create_preference_pair")


def validate_preference_pair(pair: dict) -> tuple[bool, list[str]]:
    """Validate DPO pair. Returns (valid, errors).
    Check: all keys exist, chosen != rejected, none are empty.
    # TODO:
    # 1. Check all three required keys exist: "prompt", "chosen", "rejected"
    #    Append error like "missing key: 'prompt'" for each missing key
    # 2. If all keys exist, check none are empty strings (after .strip())
    #    Append error like "'chosen' must not be empty"
    # 3. Check chosen.strip() != rejected.strip()
    #    Append error "chosen and rejected must differ"
    # 4. Return (True, []) if no errors, else (False, errors)
    """
    raise NotImplementedError("Implement validate_preference_pair")


def generate_rejection(prompt: str, chosen: str) -> str:
    """Use LLM to generate a worse version of chosen response.
    # TODO:
    # 1. Format DEGRADATION_PROMPT with prompt and chosen
    # 2. Call get_anthropic_client() and create a message with:
    #    - model=MODEL
    #    - max_tokens=512
    #    - temperature=0.7
    #    - messages=[{"role": "user", "content": formatted_prompt}]
    # 3. Return response.content[0].text.strip()
    """
    raise NotImplementedError("Implement generate_rejection")


def build_dpo_dataset(prompts: list[str]) -> list[dict]:
    """For each prompt, generate a good response (chosen) and bad response (rejected).
    # TODO:
    # 1. For each prompt:
    #    a. Call get_anthropic_client() and generate a high-quality chosen response
    #       using GOOD_RESPONSE_PROMPT (temperature=0, max_tokens=512)
    #    b. Call generate_rejection(prompt, chosen) to get the rejected response
    #    c. Call create_preference_pair(prompt, chosen, rejected) to build the pair
    #    d. Call validate_preference_pair(pair) — skip invalid pairs
    # 2. Return the list of valid pairs
    """
    raise NotImplementedError("Implement build_dpo_dataset")
