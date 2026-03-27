"""Lab 26: Self-improving Summarizer"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def generate_summary(text: str) -> str:
    """
    Generate an initial summary of the provided text.

    # TODO:
    # 1. client = get_anthropic_client()
    # 2. Call client.messages.create with a prompt that asks for a concise summary of `text`
    # 3. Return response.content[0].text
    """
    raise NotImplementedError("Implement generate_summary")


def critique_summary(original_text: str, summary: str) -> str:
    """
    Critique the summary against the original text.
    Returns a string identifying flaws.
    If there are no major issues, the returned string should contain 'NO MAJOR ISSUES'.

    # TODO:
    # 1. client = get_anthropic_client()
    # 2. Build a prompt that provides both original_text and summary, then asks the model to:
    #    - Identify key points from the original that are missing from the summary
    #    - Flag any inaccuracies or overstated claims
    #    - Note verbosity or unclear phrasing
    #    - End with the exact phrase 'NO MAJOR ISSUES' if there are no significant problems
    # 3. Return response.content[0].text
    """
    raise NotImplementedError("Implement critique_summary")


def improve_summary(text: str, max_iterations: int = 3) -> str:
    """
    Generate a summary then repeatedly critique and revise it.
    Stops when critique contains 'NO MAJOR ISSUES' or max_iterations is reached.
    Returns the final summary string.

    # TODO:
    # 1. draft = generate_summary(text)
    # 2. For up to max_iterations:
    #    a. critique_text = critique_summary(text, draft)
    #    b. If 'NO MAJOR ISSUES' in critique_text.upper(): break
    #    c. Otherwise call the LLM with a revision prompt (draft + critique_text)
    #       and update draft with the revised output
    # 3. Return draft
    """
    raise NotImplementedError("Implement improve_summary")


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
