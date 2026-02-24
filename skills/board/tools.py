from langchain_core.tools import tool


@tool
async def board_read(trip_id: str) -> str:
    """Read what's currently on the trip board. Returns a summary of all items (hotels, activities) placed on the visual canvas."""
    return "Board reading is not yet implemented. This will be available in Phase 3."


@tool
async def board_add_items(trip_id: str, items: str) -> str:
    """Add hotel or activity cards to the visual trip board. Items should be a JSON string describing what to add."""
    return "Board adding is not yet implemented. This will be available in Phase 3."


@tool
async def board_remove_items(trip_id: str, item_ids: str) -> str:
    """Remove specific items from the trip board by their IDs."""
    return "Board removal is not yet implemented. This will be available in Phase 3."


@tool
async def board_clear(trip_id: str) -> str:
    """Clear all agent-placed items from the trip board, preserving user-drawn content."""
    return "Board clearing is not yet implemented. This will be available in Phase 3."
