from pydantic import BaseModel


class BoardItem(BaseModel):
    id: str                      # Short UUID e.g. "a1b2c3d4"
    type: str                    # "stay", "activity", "flight"
    name: str                    # "Grand Hotel Lisbon"
    excalidraw_group_id: str     # Links to Excalidraw element group
    data: dict                   # Full payload (price, url, rating, imageUrl, bookingUrl, etc.)
    added_at: str                # ISO timestamp
