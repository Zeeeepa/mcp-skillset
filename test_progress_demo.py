#!/usr/bin/env python3
"""Demo script to test per-repository progress bars."""

import tempfile
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from mcp_skills.services.repository_manager import RepositoryManager


def main() -> None:
    """Test progress bar functionality with actual repository clone."""
    console = Console()
    console.print("[bold]Testing Per-Repository Progress Bars[/bold]\n")

    # Use temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        repo_manager = RepositoryManager(base_dir=base_dir)

        # Test data: small repository that clones quickly
        test_repos = [
            {
                "url": "https://github.com/anthropics/anthropic-quickstarts.git",
                "priority": 100,
                "license": "MIT",
            }
        ]

        console.print(
            "[bold cyan]Testing repository clone with progress bar...[/bold cyan]\n"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            for repo_config in test_repos:
                # Extract repo name from URL for display
                repo_name = repo_config["url"].split("/")[-1].replace(".git", "")

                # Create task for this repository
                task_id = progress.add_task(
                    f"Cloning {repo_name}",
                    total=100,
                    start=False,
                )

                # Progress callback updates this specific task
                def make_callback(tid: int):
                    def update_progress(current: int, total: int, message: str) -> None:
                        if total > 0:
                            progress.update(tid, completed=current, total=total)
                            if not progress.tasks[tid].started:
                                progress.start_task(tid)

                    return update_progress

                try:
                    new_repo = repo_manager.add_repository_with_progress(
                        url=repo_config["url"],
                        priority=repo_config["priority"],
                        license=repo_config.get("license", "Unknown"),
                        progress_callback=make_callback(task_id),
                    )
                    progress.update(
                        task_id, description=f"✓ {repo_name}", completed=100
                    )
                    console.print(f"\n[green]✓[/green] Successfully cloned {repo_name}")
                    console.print(f"  • ID: {new_repo.id}")
                    console.print(f"  • Skills: {new_repo.skill_count}")
                    console.print(f"  • Path: {new_repo.local_path}\n")
                except Exception as e:
                    progress.update(task_id, description=f"✗ {repo_name}")
                    console.print(f"\n[red]✗[/red] Failed to clone {repo_name}: {e}\n")

        console.print("[bold green]✓ Progress bar test completed![/bold green]")


if __name__ == "__main__":
    main()
