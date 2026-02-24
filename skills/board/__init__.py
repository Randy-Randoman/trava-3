"""Board management — read, add, remove items from the Excalidraw canvas."""
from .tools import board_read, board_add_items, board_remove_items, board_clear

TOOLS = [board_read, board_add_items, board_remove_items, board_clear]
PROMPT = """You can manage the visual trip board:
- board_read: See what's currently on the board
- board_add_items: Place hotel/activity cards on the canvas
- board_remove_items: Remove specific items by ID
- board_clear: Remove all agent-placed items
Note: Board tools are placeholders in Phase 2 — they acknowledge the request but don't modify the canvas yet."""
