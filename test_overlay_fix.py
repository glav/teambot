#!/usr/bin/env python3
"""Manual test script for overlay scrolling fix.

This script demonstrates the overlay staying fixed while output scrolls.
Press Enter multiple times to see if the overlay remains at the top.
"""

import time
import sys
from rich.console import Console
from src.teambot.visualization.overlay import OverlayRenderer, OverlayPosition


def main():
    console = Console()
    
    # Create overlay at top-right (the problematic position)
    overlay = OverlayRenderer(console=console, position=OverlayPosition.TOP_RIGHT)
    
    if not overlay.is_supported:
        console.print("[red]Overlay not supported in this terminal[/red]")
        return
    
    # Enable overlay and simulate activity
    overlay.enable()
    overlay.update_state(
        active_agents=["builder-1", "reviewer"],
        running_count=2,
        pending_count=1,
        completed_count=5,
    )
    
    console.print("\n[bold cyan]Overlay Scrolling Fix Test[/bold cyan]")
    console.print("The status box should stay fixed at the top-right corner.")
    console.print("Press Enter to generate output and test scrolling...")
    console.print("Type 'quit' to exit.\n")
    
    line_count = 1
    try:
        while True:
            user_input = input(f"[{line_count}] > ")
            
            if user_input.lower() in ('quit', 'exit', 'q'):
                break
            
            # Simulate output that would normally scroll
            overlay.print_with_overlay(
                f"[green]✓[/green] Generated output line {line_count}"
            )
            
            # Update spinner to show animation
            overlay.advance_spinner()
            
            line_count += 1
            
            # Simulate some task completion
            if line_count % 3 == 0:
                overlay.update_state(completed_count=overlay.state.completed_count + 1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    
    finally:
        # Clean up
        overlay.disable()
        console.print("\n[bold green]Test complete![/bold green]")
        console.print("Did the overlay stay fixed at the top? ✓")


if __name__ == "__main__":
    main()
