import json
from datetime import datetime, timezone
from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState


def _generate_id() -> str:
    """Generate a short unique ID for board items."""
    import uuid
    return str(uuid.uuid4())[:8]


@tool
async def board_read(trip_id: Annotated[str, InjectedState("trip_id")]) -> str:
    """Read what's currently on the trip board. Returns a summary of all items (hotels, activities) placed on the visual canvas."""
    from app.services.database import DatabaseService

    db = DatabaseService()
    items = await db.get_board_items(trip_id)

    if not items:
        return "Board is empty. No items have been added yet."

    lines = [f"Board has {len(items)} item(s):"]
    for item in items:
        item_id = item.get("id", "?")[:4]
        item_type = item.get("type", "item").upper()
        name = item.get("name", "Unnamed")
        data = item.get("data", {})

        details = []
        if data.get("price"):
            details.append(data["price"])
        if data.get("rating"):
            details.append(f"Rating: {data['rating']}")
        if data.get("review_count"):
            details.append(f"{data['review_count']} reviews")

        detail_str = f" ({', '.join(details)})" if details else ""
        lines.append(f"- [{item_id}] {item_type}: {name}{detail_str}")

    return "\n".join(lines)


@tool
async def board_add_items(
    items: str,
    trip_id: Annotated[str, InjectedState("trip_id")],
) -> str:
    """Add hotel or activity cards to the visual trip board.

    Args:
        items: JSON string — a list of item objects. Each object should have:
            name (required), type ("stay"/"activity"), price, rating, review_count,
            distance, url/bookingUrl, image_url/imageUrl.
            Optional: day (int, e.g. 1), date (str, e.g. "2026-03-17") for day grouping.
    """
    from app.services.database import DatabaseService
    from app.logic.transformer import generate_card_elements

    # Parse items JSON
    try:
        item_list = json.loads(items) if isinstance(items, str) else items
        if not isinstance(item_list, list):
            item_list = [item_list]
    except json.JSONDecodeError as e:
        return f"Error: Could not parse items JSON: {e}"

    if not item_list:
        return "Error: No items provided."

    db = DatabaseService()

    # Read current canvas state
    canvas = await db.get_canvas_state(trip_id)
    existing_elements = []
    existing_files = {}
    if canvas:
        existing_elements = canvas.get("scene_elements") or []
        existing_files = canvas.get("scene_files") or {}

    # Read current board items
    current_board_items = await db.get_board_items(trip_id)

    # Generate card elements positioned below existing content
    new_elements, new_files, group_ids = await generate_card_elements(
        item_list, existing_elements
    )

    # Append new elements to existing canvas
    updated_elements = existing_elements + new_elements

    # Merge new files into existing files
    updated_files = {**existing_files, **new_files}

    # Save updated canvas state
    await db.update_canvas_state(
        trip_id,
        scene_elements=updated_elements,
        scene_files=updated_files,
    )

    # Create BoardItem records for tracking
    new_board_items = []
    for i, item in enumerate(item_list):
        board_item = {
            "id": _generate_id(),
            "type": item.get("type", "stay"),
            "name": item.get("name", "Unnamed"),
            "day": item.get("day"),
            "date": item.get("date"),
            "excalidraw_group_id": group_ids[i] if i < len(group_ids) else _generate_id(),
            "data": item,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        new_board_items.append(board_item)

    # Save updated board items
    await db.update_board_items(trip_id, current_board_items + new_board_items)

    names = [item.get("name", "item") for item in item_list]
    return f"Added {len(item_list)} item(s) to the board: {', '.join(names)}"


@tool
async def board_remove_items(
    item_ids: str,
    trip_id: Annotated[str, InjectedState("trip_id")],
) -> str:
    """Remove specific items from the trip board by their IDs (the short IDs shown by board_read, e.g. 'a1b2').

    Args:
        item_ids: Comma-separated item IDs to remove (e.g. "a1b2,c3d4")
    """
    from app.services.database import DatabaseService

    # Parse item IDs
    ids_to_remove = [id.strip() for id in item_ids.split(",") if id.strip()]
    if not ids_to_remove:
        return "Error: No item IDs provided."

    db = DatabaseService()
    board_items = await db.get_board_items(trip_id)

    if not board_items:
        return "Board is empty, nothing to remove."

    # Find items to remove (match by ID prefix — board_read shows first 4 chars)
    items_to_remove = []
    group_ids_to_remove = set()
    for bi in board_items:
        bi_id = bi.get("id", "")
        if any(bi_id.startswith(rid) for rid in ids_to_remove):
            items_to_remove.append(bi)
            group_ids_to_remove.add(bi.get("excalidraw_group_id"))

    if not items_to_remove:
        return f"No items found matching IDs: {', '.join(ids_to_remove)}"

    # Filter out canvas elements with those group IDs
    canvas = await db.get_canvas_state(trip_id)
    if canvas and canvas.get("scene_elements"):
        elements = canvas["scene_elements"]
        filtered = [
            el for el in elements
            if not any(gid in (el.get("groupIds") or []) for gid in group_ids_to_remove)
        ]
        await db.update_canvas_state(trip_id, scene_elements=filtered)

    # Remove items from board_items
    remaining = [bi for bi in board_items if bi not in items_to_remove]
    await db.update_board_items(trip_id, remaining)

    names = [bi.get("name", "item") for bi in items_to_remove]
    return f"Removed {len(items_to_remove)} item(s) from the board: {', '.join(names)}"


@tool
async def board_clear(trip_id: Annotated[str, InjectedState("trip_id")]) -> str:
    """Clear all agent-placed items from the trip board, preserving user-drawn content."""
    from app.services.database import DatabaseService

    db = DatabaseService()
    board_items = await db.get_board_items(trip_id)

    if not board_items:
        return "Board is already empty."

    # Collect all group IDs from agent-placed items
    group_ids_to_remove = set()
    for bi in board_items:
        gid = bi.get("excalidraw_group_id")
        if gid:
            group_ids_to_remove.add(gid)

    # Filter out agent-placed elements from canvas (preserves user-drawn content)
    canvas = await db.get_canvas_state(trip_id)
    if canvas and canvas.get("scene_elements"):
        elements = canvas["scene_elements"]
        filtered = [
            el for el in elements
            if not any(gid in (el.get("groupIds") or []) for gid in group_ids_to_remove)
        ]
        await db.update_canvas_state(trip_id, scene_elements=filtered)

    count = len(board_items)
    await db.update_board_items(trip_id, [])

    return f"Cleared {count} item(s) from the board. User-drawn content preserved."
