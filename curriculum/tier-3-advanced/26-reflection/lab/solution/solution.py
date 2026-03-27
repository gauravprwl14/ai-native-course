"""Lab 26: Self-improving Summarizer — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def generate_summary(text: str) -> str:
    """Generate an initial summary of the provided text."""
    client = get_anthropic_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write a concise summary of the following text in 3-5 sentences:\n\n{text}"
                ),
            }
        ],
    )
    return response.content[0].text


def critique_summary(original_text: str, summary: str) -> str:
    """
    Critique the summary against the original text.
    Returns feedback string. Contains 'NO MAJOR ISSUES' if the summary is satisfactory.
    """
    client = get_anthropic_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Original text:\n{original_text}\n\n"
                    f"Summary to evaluate:\n{summary}\n\n"
                    "Critique this summary. Specifically:\n"
                    "1. List any key points from the original that are missing\n"
                    "2. Flag any inaccuracies or overstated claims\n"
                    "3. Note any verbosity or unclear phrasing\n\n"
                    "If there are no significant problems, end your response with the exact phrase: "
                    "NO MAJOR ISSUES"
                ),
            }
        ],
    )
    return response.content[0].text


def _revise(original_text: str, draft: str, critique_text: str) -> str:
    """Revise the draft to address the identified issues."""
    client = get_anthropic_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Original text:\n{original_text}\n\n"
                    f"Current summary:\n{draft}\n\n"
                    f"Issues identified:\n{critique_text}\n\n"
                    "Write an improved summary that addresses all the identified issues. "
                    "Output only the revised summary, no meta-commentary."
                ),
            }
        ],
    )
    return response.content[0].text


def improve_summary(text: str, max_iterations: int = 3) -> str:
    """
    Generate a summary, then repeatedly critique and revise it.
    Stops when critique returns 'NO MAJOR ISSUES' or max_iterations is reached.
    Returns the final summary string.
    """
    draft = generate_summary(text)

    for _ in range(max_iterations):
        critique_text = critique_summary(text, draft)
        if "NO MAJOR ISSUES" in critique_text.upper():
            break
        draft = _revise(text, draft, critique_text)

    return draft


if __name__ == "__main__":
    sample_text = """
    Machine learning is a subset of artificial intelligence that enables systems to learn from
    data without being explicitly programmed. Supervised learning uses labelled training data
    to learn a mapping from inputs to outputs. Unsupervised learning finds hidden patterns in
    data without labels. Reinforcement learning trains agents through reward and penalty signals.
    Deep learning, a subset of machine learning, uses neural networks with many layers to learn
    hierarchical representations from large datasets.
    """

    print("Generating initial summary...")
    initial = generate_summary(sample_text)
    print("Initial:", initial)

    print("\nCritiquing...")
    feedback = critique_summary(sample_text, initial)
    print("Critique:", feedback)

    print("\nRunning full G-C-R loop...")
    final = improve_summary(sample_text, max_iterations=2)
    print("Final summary:", final)
