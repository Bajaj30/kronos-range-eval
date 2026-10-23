"""Regenerate FACTS.md from config.py and out/facts/*.json. Run after any step that writes facts."""
import config
from lib.facts import render


def main():
    text = render(config, config.FACTS_DIR)
    config.FACTS_MD.write_text(text)
    # Self-check: a second render must be byte-identical (deterministic output).
    assert render(config, config.FACTS_DIR) == config.FACTS_MD.read_text(), "FACTS.md render is not deterministic"
    print(f"wrote {config.FACTS_MD.name}: {len(text.splitlines())} lines")


if __name__ == "__main__":
    main()
