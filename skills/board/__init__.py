"""Board management — read, add, remove items from the Excalidraw canvas."""
from .tools import board_read, board_add_items, board_remove_items, board_clear

TOOLS = [board_read, board_add_items, board_remove_items, board_clear]
PROMPT = """You can manage the visual trip board:
- board_read: See what's currently on the board (returns item IDs and details)
- board_add_items: Place hotel/activity cards on the canvas. Pass a JSON string with a list of items (each with name, type, price, rating, etc.)
- board_remove_items: Remove specific items by their short IDs (shown by board_read)
- board_clear: Remove all agent-placed items, preserving user drawings
When the user asks to add search results to the board, use board_add_items with the hotel data from the search results."""
