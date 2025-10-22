#!/usr/bin/env python3
"""
kAIcad Launcher - Interactive interface selector

Provides a simple menu to choose between CLI, Desktop (Tkinter), and Web interfaces.
"""

import sys
from typing import Optional


def print_banner():
    """Display the kAIcad banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██╗  ██╗ █████╗ ██╗ ██████╗ █████╗ ██████╗              ║
║   ██║ ██╔╝██╔══██╗██║██╔════╝██╔══██╗██╔══██╗             ║
║   █████╔╝ ███████║██║██║     ███████║██║  ██║             ║
║   ██╔═██╗ ██╔══██║██║██║     ██╔══██║██║  ██║             ║
║   ██║  ██╗██║  ██║██║╚██████╗██║  ██║██████╔╝             ║
║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝              ║
║                                                              ║
║         AI-powered sidecar for KiCad schematics              ║
║                      Version 0.1.0                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_menu():
    """Display the interface selection menu."""
    print("\nChoose your interface:\n")
    print("  [1] CLI         - Command-line interface for quick operations")
    print("  [2] Desktop     - Tkinter GUI for local desktop usage")
    print("  [3] Web         - Flask web interface (default port 5173)")
    print()
    print("  [q] Quit\n")


def launch_cli():
    """Launch the CLI interface."""
    try:
        from kaicad.ui.cli import main as cli_main
        print("\n🚀 Launching CLI interface...")
        print("=" * 60)
        cli_main()
    except ImportError as e:
        print(f"❌ Failed to import CLI module: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 CLI interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ CLI error: {e}")
        sys.exit(1)


def launch_desktop():
    """Launch the Desktop (Tkinter) interface."""
    try:
        from kaicad.ui.desktop import main as desktop_main
        print("\n🚀 Launching Desktop interface...")
        print("=" * 60)
        desktop_main()
    except ImportError as e:
        print(f"❌ Failed to import Desktop module: {e}")
        print("💡 Tip: Tkinter should be included with Python, but may need separate installation on some systems.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Desktop interface interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Desktop interface error: {e}")
        sys.exit(1)


def launch_web():
    """Launch the Web (Flask) interface."""
    try:
        from kaicad.ui.web.app import main as web_main
        print("\n🚀 Launching Web interface...")
        print("=" * 60)
        print("💡 The web interface will start on http://localhost:5173")
        print("   Press Ctrl+C to stop the server")
        print("=" * 60)
        web_main()
    except ImportError as e:
        print(f"❌ Failed to import Web module: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Web server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Web interface error: {e}")
        sys.exit(1)


def get_user_choice() -> Optional[str]:
    """
    Get user's interface choice.
    
    Returns:
        User's choice ('1', '2', '3', 'q') or None if invalid
    """
    try:
        choice = input("Enter your choice: ").strip().lower()
        return choice
    except (EOFError, KeyboardInterrupt):
        return 'q'


def main():
    """Main launcher entry point."""
    # Handle command-line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--cli', '-c', 'cli']:
            launch_cli()
            return
        elif arg in ['--desktop', '-d', 'desktop', 'desk']:
            launch_desktop()
            return
        elif arg in ['--web', '-w', 'web']:
            launch_web()
            return
        elif arg in ['--help', '-h', 'help']:
            print("kAIcad Launcher - Interface selector\n")
            print("Usage:")
            print("  kaicad              Launch interactive menu")
            print("  kaicad --cli        Launch CLI interface directly")
            print("  kaicad --desktop    Launch Desktop interface directly")
            print("  kaicad --web        Launch Web interface directly")
            print("  kaicad --help       Show this help message")
            print("\nAlternative commands:")
            print("  kaicad-cli          CLI interface (same as 'kaicad --cli')")
            print("  kaicad-desk         Desktop interface")
            print("  kaicad-web          Web interface")
            return
        else:
            print(f"❌ Unknown option: {arg}")
            print("Use 'kaicad --help' for usage information")
            sys.exit(1)
    
    # Interactive menu
    try:
        print_banner()
        
        while True:
            print_menu()
            choice = get_user_choice()
            
            if choice == '1':
                launch_cli()
                break
            elif choice == '2':
                launch_desktop()
                break
            elif choice == '3':
                launch_web()
                break
            elif choice == 'q':
                print("\n👋 Goodbye!")
                sys.exit(0)
            else:
                print(f"\n❌ Invalid choice: '{choice}'. Please enter 1, 2, 3, or q.\n")
    
    except KeyboardInterrupt:
        print("\n\n👋 Launcher interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
