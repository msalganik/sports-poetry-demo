#!/usr/bin/env python3
"""
Poetry Generation Agent

Generates a haiku and sonnet about a given sport.
In a production system, this would call an LLM API (e.g., Claude, GPT-4).
For this demo, we use template-based generation.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime


# Simple template-based poem generation for demo purposes
# In production, replace with actual LLM API calls

HAIKU_TEMPLATES = {
    "basketball": [
        "Orange sphere in flight,",
        "Swish through the net, crowd erupts—",
        "Victory is sweet."
    ],
    "soccer": [
        "Feet dance with the ball,",
        "Green field, one goal, hearts racing—",
        "Strike! The net trembles."
    ],
    "tennis": [
        "Yellow blur flies fast,",
        "Racket meets ball, rally grows—",
        "Match point, pure silence."
    ],
    "football": [
        "Pigskin spirals high,",
        "Eleven warriors clash hard—",
        "Touchdown brings triumph."
    ],
    "baseball": [
        "Crack of bat on ball,",
        "Diamond dust, runners flying—",
        "Home plate calls them back."
    ],
    "hockey": [
        "Blades carve frozen ice,",
        "Puck speeds past the goalie's mask—",
        "Horn sounds, game is won."
    ],
    "volleyball": [
        "Hands raised, ball soars high,",
        "Spike! It crashes to the ground—",
        "Sand flies, point is won."
    ],
    "swimming": [
        "Blue water awaits,",
        "Streamlined form cuts through the waves—",
        "Touch the wall, breathe deep."
    ],
    "default": [
        "Athletes prepare well,",
        "Competition fuels their fire—",
        "Glory awaits all."
    ]
}

SONNET_TEMPLATES = {
    "basketball": [
        "Upon the hardwood court where giants play,",
        "The leather sphere ascends with graceful arc,",
        "Through defenders' hands it finds its way,",
        "Each dribble, pass, and shot leaves its mark.",
        "",
        "The crowd erupts when three points find the net,",
        "While fast breaks surge like lightning down the floor,",
        "In overtime when rivals clash and sweat,",
        "The game reveals what hearts are beating for.",
        "",
        "With every season, legends rise and fall,",
        "The championship ring, the ultimate prize,",
        "Yet in the beauty of that bouncing ball,",
        "We see humanities truths before our eyes:",
        "  That teamwork, skill, and passion intertwine,",
        "  In basketball, these virtues brightly shine."
    ],
    "soccer": [
        "The beautiful game on grass so green and wide,",
        "Where twenty-two souls chase one checkered sphere,",
        "With skillful feet they dribble, pass with pride,",
        "While millions watch and fill the stands with cheer.",
        "",
        "From youth who dream beneath the favela sun,",
        "To stadium lights that pierce the evening sky,",
        "The quest for goals has just begun—",
        "Watch strikers surge as corner kicks fly high.",
        "",
        "The goalkeeper stands alone, the last defense,",
        "While midfield generals orchestrate the play,",
        "Each match contains such drama, so intense,",
        "That ninety minutes feel like one long day.",
        "  When final whistle blows and scores are set,",
        "  These memories we'll never quite forget."
    ],
    "default": [
        "In sport we find humanity expressed,",
        "The striving for excellence and for grace,",
        "Where athletes put their abilities to test,",
        "And push beyond what limits once held place.",
        "",
        "Through years of practice, discipline, and pain,",
        "They forge their bodies into perfect tools,",
        "The victories and losses, sun and rain,",
        "All teach them lessons not found in schools.",
        "",
        "Spectators gather, drawn by this display,",
        "Of human potential pushed to its extreme,",
        "We cheer for those who show us how to play,",
        "With honor, passion, pursuing their dream.",
        "  In every sport, we see ourselves reflected,",
        "  Our hopes and struggles, beautifully projected."
    ]
}


def generate_haiku_together(sport: str, model: str, api_token: str) -> list:
    """Generate a haiku using Together.ai API."""
    try:
        from together import Together
    except ImportError:
        raise ImportError(
            "together is required for Together.ai. "
            "Install it with: pip install -r requirements.txt"
        )

    client = Together(api_key=api_token)

    prompt = f"""Write a haiku about {sport}.
Follow the traditional 5-7-5 syllable structure.
Capture the essence and excitement of the sport.
Return only the haiku, no other text."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        # Extract text from response
        text = response.choices[0].message.content
        # Parse response into lines
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        # Return first 3 non-empty lines
        return lines[:3] if len(lines) >= 3 else lines
    except Exception as e:
        raise RuntimeError(f"Together.ai API error: {e}")


def generate_sonnet_together(sport: str, model: str, api_token: str) -> list:
    """Generate a sonnet using Together.ai API."""
    try:
        from together import Together
    except ImportError:
        raise ImportError(
            "together is required for Together.ai. "
            "Install it with: pip install -r requirements.txt"
        )

    client = Together(api_key=api_token)

    prompt = f"""Write a 14-line sonnet about {sport}.
Use iambic pentameter if possible.
Explore deeper themes of competition, skill, and human achievement.
Return only the sonnet, no other text."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        # Extract text from response
        text = response.choices[0].message.content
        # Parse response into lines
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        return lines
    except Exception as e:
        raise RuntimeError(f"Together.ai API error: {e}")


def generate_haiku_llm(sport: str, model: str, api_token: str) -> list:
    """Generate a haiku using HuggingFace Inference API."""
    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        raise ImportError(
            "huggingface-hub is required for LLM mode. "
            "Install it with: pip install -r requirements.txt"
        )

    client = InferenceClient(token=api_token)

    prompt = f"""Write a haiku about {sport}.
Follow the traditional 5-7-5 syllable structure.
Capture the essence and excitement of the sport.
Return only the haiku, no other text."""

    try:
        response = client.text_generation(
            prompt,
            model=model,
            max_new_tokens=100,
            temperature=0.7
        )
        # Parse response into lines
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        # Return first 3 non-empty lines
        return lines[:3] if len(lines) >= 3 else lines
    except Exception as e:
        raise RuntimeError(f"HuggingFace API error: {e}")


def generate_sonnet_llm(sport: str, model: str, api_token: str) -> list:
    """Generate a sonnet using HuggingFace Inference API."""
    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        raise ImportError(
            "huggingface-hub is required for LLM mode. "
            "Install it with: pip install -r requirements.txt"
        )

    client = InferenceClient(token=api_token)

    prompt = f"""Write a 14-line sonnet about {sport}.
Use iambic pentameter if possible.
Explore deeper themes of competition, skill, and human achievement.
Return only the sonnet, no other text."""

    try:
        response = client.text_generation(
            prompt,
            model=model,
            max_new_tokens=300,
            temperature=0.7
        )
        # Parse response into lines
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        return lines
    except Exception as e:
        raise RuntimeError(f"HuggingFace API error: {e}")


def generate_haiku(sport: str, generation_mode: str = "template",
                  llm_model: str = None, api_token: str = None, llm_provider: str = "huggingface") -> list:
    """Generate a haiku about the sport (5-7-5 syllable structure)."""
    if generation_mode == "llm":
        if not api_token:
            raise ValueError(
                f"LLM mode requires API token environment variable. "
                f"For Together.ai: TOGETHER_API_KEY, For HuggingFace: HUGGINGFACE_API_TOKEN"
            )
        if not llm_model:
            raise ValueError("LLM mode requires llm_model in config")

        # Route to appropriate provider
        if llm_provider == "together":
            return generate_haiku_together(sport, llm_model, api_token)
        else:  # default to huggingface
            return generate_haiku_llm(sport, llm_model, api_token)
    else:
        # Template mode (default)
        template = HAIKU_TEMPLATES.get(sport.lower(), HAIKU_TEMPLATES["default"])
        return template


def generate_sonnet(sport: str, generation_mode: str = "template",
                   llm_model: str = None, api_token: str = None, llm_provider: str = "huggingface") -> list:
    """Generate a 14-line sonnet about the sport."""
    if generation_mode == "llm":
        if not api_token:
            raise ValueError(
                f"LLM mode requires API token environment variable. "
                f"For Together.ai: TOGETHER_API_KEY, For HuggingFace: HUGGINGFACE_API_TOKEN"
            )
        if not llm_model:
            raise ValueError("LLM mode requires llm_model in config")

        # Route to appropriate provider
        if llm_provider == "together":
            return generate_sonnet_together(sport, llm_model, api_token)
        else:  # default to huggingface
            return generate_sonnet_llm(sport, llm_model, api_token)
    else:
        # Template mode (default)
        template = SONNET_TEMPLATES.get(sport.lower(), SONNET_TEMPLATES["default"])
        return template


def count_words(lines: list) -> int:
    """Count total words in poem."""
    return sum(len(line.split()) for line in lines)


def main():
    import os

    if len(sys.argv) < 2:
        print("Error: Sport name required", file=sys.stderr)
        sys.exit(1)

    sport = sys.argv[1]
    session_dir = sys.argv[2] if len(sys.argv) > 2 else "output"  # Default for backward compat
    config_path = sys.argv[3] if len(sys.argv) > 3 else "config.json"  # Config file path

    start_time = time.time()

    # Load config
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error: Could not load config: {e}", file=sys.stderr)
        sys.exit(1)

    # Get generation settings
    generation_mode = config.get("generation_mode", "template")
    llm_provider = config.get("llm_provider", "together")
    llm_model = config.get("llm_model", "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free")

    # Get appropriate API token based on provider
    if llm_provider == "together":
        api_token = os.environ.get("TOGETHER_API_KEY")
    else:
        api_token = os.environ.get("HUGGINGFACE_API_TOKEN")

    print(f"Agent {sport}: Starting poetry generation (mode: {generation_mode}, provider: {llm_provider})")

    # Create output directory within session
    output_dir = Path(session_dir) / sport
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate haiku
    try:
        haiku_lines = generate_haiku(sport, generation_mode, llm_model, api_token, llm_provider)
    except Exception as e:
        print(f"Error generating haiku: {e}", file=sys.stderr)
        sys.exit(1)

    haiku_text = "\n".join(haiku_lines)

    # Write haiku
    haiku_file = output_dir / "haiku.txt"
    with open(haiku_file, "w") as f:
        f.write(haiku_text + "\n")

    print(f"Agent {sport}: Wrote haiku ({len(haiku_lines)} lines)")

    # Generate sonnet
    try:
        sonnet_lines = generate_sonnet(sport, generation_mode, llm_model, api_token, llm_provider)
    except Exception as e:
        print(f"Error generating sonnet: {e}", file=sys.stderr)
        sys.exit(1)

    sonnet_text = "\n".join(sonnet_lines)

    # Write sonnet
    sonnet_file = output_dir / "sonnet.txt"
    with open(sonnet_file, "w") as f:
        f.write(sonnet_text + "\n")

    print(f"Agent {sport}: Wrote sonnet ({len(sonnet_lines)} lines)")

    # Create metadata
    end_time = time.time()
    metadata = {
        "sport": sport,
        "generation_mode": generation_mode,
        "llm_model": llm_model if generation_mode == "llm" else None,
        "timestamp_start": datetime.utcnow().isoformat() + "Z",
        "timestamp_end": datetime.utcnow().isoformat() + "Z",
        "duration_s": round(end_time - start_time, 2),
        "haiku_lines": len(haiku_lines),
        "haiku_words": count_words(haiku_lines),
        "sonnet_lines": len(sonnet_lines),
        "sonnet_words": count_words(sonnet_lines)
    }

    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Agent {sport}: Complete")


if __name__ == "__main__":
    main()
