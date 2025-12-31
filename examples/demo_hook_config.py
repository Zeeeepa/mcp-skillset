#!/usr/bin/env python3
"""Demo script showing the hook configuration menu in action.

This script demonstrates the new hook configuration features added to ConfigMenu.

Usage:
    python examples/demo_hook_config.py
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from mcp_skills.cli.config_menu import ConfigMenu


def demo_view_hook_config():
    """Demo 1: View current hook configuration."""
    print("=" * 60)
    print("DEMO 1: View Current Hook Configuration")
    print("=" * 60)

    menu = ConfigMenu()

    print("\nCurrent hook settings:")
    print(f"  • Enabled: {menu.config.hooks.enabled}")
    print(f"  • Threshold: {menu.config.hooks.threshold}")
    print(f"  • Max skills: {menu.config.hooks.max_skills}")
    print()


def demo_toggle_hooks():
    """Demo 2: Toggle hooks enabled/disabled."""
    print("=" * 60)
    print("DEMO 2: Toggle Hooks (Disable)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        with patch.object(ConfigMenu, "CONFIG_PATH", config_path):
            menu = ConfigMenu()

            print(f"\nBefore: enabled = {menu.config.hooks.enabled}")

            # Simulate disabling hooks
            with patch("mcp_skills.cli.config_menu.questionary.confirm") as mock_confirm:
                mock_confirm.return_value.ask.return_value = False
                menu._toggle_hooks()

            print(f"After: enabled = {menu.config.hooks.enabled}")
            print()


def demo_configure_threshold():
    """Demo 3: Configure hook threshold."""
    print("=" * 60)
    print("DEMO 3: Configure Threshold")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        with patch.object(ConfigMenu, "CONFIG_PATH", config_path):
            menu = ConfigMenu()

            print(f"\nBefore: threshold = {menu.config.hooks.threshold}")

            # Simulate setting threshold to 0.8
            with patch("mcp_skills.cli.config_menu.questionary.text") as mock_text:
                mock_text.return_value.ask.return_value = "0.8"
                menu._configure_hook_threshold()

            print(f"After: threshold = {menu.config.hooks.threshold}")
            print()


def demo_configure_max_skills():
    """Demo 4: Configure max skills."""
    print("=" * 60)
    print("DEMO 4: Configure Max Skills")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        with patch.object(ConfigMenu, "CONFIG_PATH", config_path):
            menu = ConfigMenu()

            print(f"\nBefore: max_skills = {menu.config.hooks.max_skills}")

            # Simulate setting max skills to 8
            with patch("mcp_skills.cli.config_menu.questionary.text") as mock_text:
                mock_text.return_value.ask.return_value = "8"
                menu._configure_hook_max_skills()

            print(f"After: max_skills = {menu.config.hooks.max_skills}")
            print()


def demo_validation():
    """Demo 5: Input validation."""
    print("=" * 60)
    print("DEMO 5: Input Validation")
    print("=" * 60)

    print("\nTesting max_skills validation:")
    print(f"  • '5' (valid): {ConfigMenu._validate_max_skills('5')}")
    print(f"  • '0' (invalid): {ConfigMenu._validate_max_skills('0')}")
    print(f"  • '11' (invalid): {ConfigMenu._validate_max_skills('11')}")
    print(f"  • 'abc' (invalid): {ConfigMenu._validate_max_skills('abc')}")

    print("\nTesting threshold validation:")
    print(f"  • '0.6' (valid): {ConfigMenu._validate_weight('0.6')}")
    print(f"  • '1.1' (invalid): {ConfigMenu._validate_weight('1.1')}")
    print(f"  • '-0.1' (invalid): {ConfigMenu._validate_weight('-0.1')}")
    print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Hook Configuration Menu Demo" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    demo_view_hook_config()
    demo_toggle_hooks()
    demo_configure_threshold()
    demo_configure_max_skills()
    demo_validation()

    print("=" * 60)
    print("All demos completed successfully!")
    print("=" * 60)
    print()
    print("To use the interactive menu, run:")
    print("  mcp-skillset config")
    print()
    print("Then select: 'Hook settings (Claude Code integration)'")
    print()


if __name__ == "__main__":
    main()
