"""
Transformer Engine - Converts Trip JSON to Excalidraw JSON

This module implements a Masonry Layout Algorithm to position
travel cards (stays, activities) on an Excalidraw canvas.
"""

import logging
import uuid
import httpx
from typing import Dict, List, Any, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)


# ================================================
# Default Layout Constants (for 65% of 1920px screen)
# ================================================
DEFAULT_VIEWPORT_WIDTH = 1248  # 65% of 1920
DEFAULT_VIEWPORT_HEIGHT = 900
DEFAULT_COLUMN_COUNT = 3
GAP = 20
PADDING = 16
IMAGE_HEIGHT = 150
FONT_SIZE = 16
LINE_HEIGHT = 1.4
CHAR_WIDTH = 10  # Approximate pixels per character (increased for Excalidraw font)


def validate_url(url: str) -> bool:
    """Basic URL validation"""
    if not url:
        return False
    return url.startswith("http://") or url.startswith("https://")


def sanitize_url(url: str) -> Optional[str]:
    """Sanitize and validate a URL, returning None if invalid"""
    if not url or not validate_url(url):
        return None
    return url


async def search_tavily_image(query: str) -> Optional[str]:
    """
    Search for a real image using Tavily API (async version).

    Args:
        query: Search query for the image

    Returns:
        Image URL or None
    """
    try:
        api_key = settings.TAVILY_API_KEY
        if not api_key:
            return None

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "include_images": True,
                    "max_results": 3
                }
            )
            response.raise_for_status()
            data = response.json()
            images = data.get("images", [])
            if images:
                logger.info(f"Tavily found image for '{query}': {images[0][:60]}...")
                return images[0]
    except Exception as e:
        logger.warning(f"Tavily image search failed for '{query}': {e}")

    return None


def wrap_text(text: str, max_chars_per_line: int) -> str:
    """
    Wrap text to fit within a maximum character width per line.
    Preserves existing newlines and wraps long lines.

    Args:
        text: The text to wrap
        max_chars_per_line: Maximum characters per line

    Returns:
        Text with newlines inserted for wrapping
    """
    if not text:
        return text

    wrapped_lines = []
    for paragraph in text.split('\n'):
        if not paragraph:
            wrapped_lines.append('')
            continue

        # Wrap this paragraph
        words = paragraph.split(' ')
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)

            # If adding this word exceeds the limit
            if current_length + word_length + (1 if current_line else 0) > max_chars_per_line:
                if current_line:
                    wrapped_lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    # Word is longer than max - force break it
                    while len(word) > max_chars_per_line:
                        wrapped_lines.append(word[:max_chars_per_line])
                        word = word[max_chars_per_line:]
                    if word:
                        current_line = [word]
                        current_length = len(word)
            else:
                current_line.append(word)
                current_length += word_length + (1 if len(current_line) > 1 else 0)

        if current_line:
            wrapped_lines.append(' '.join(current_line))

    return '\n'.join(wrapped_lines)


def calculate_layout_params(viewport_width: int = DEFAULT_VIEWPORT_WIDTH, viewport_height: int = DEFAULT_VIEWPORT_HEIGHT):
    """
    Calculate responsive layout parameters based on viewport size

    Args:
        viewport_width: Available width for the canvas
        viewport_height: Available height for the canvas

    Returns:
        Dict with column_width, column_count, gap, padding
    """
    # Responsive column count based on width
    if viewport_width < 600:
        column_count = 1
    elif viewport_width < 900:
        column_count = 2
    else:
        column_count = 3

    # Calculate column width with margins
    total_gap = GAP * (column_count + 1)
    column_width = (viewport_width - total_gap) // column_count

    # Scale image height based on column width
    image_height = min(150, int(column_width * 0.5))

    return {
        'column_width': column_width,
        'column_count': column_count,
        'gap': GAP,
        'padding': PADDING,
        'image_height': image_height,
        'viewport_width': viewport_width,
        'viewport_height': viewport_height
    }


# ================================================
# Excalidraw Element Factories
# ================================================

def _generate_id() -> str:
    """Generate a unique element ID"""
    return str(uuid.uuid4())[:8]


def _create_rectangle(
    x: float,
    y: float,
    width: float,
    height: float,
    fill_color: str = "#ffffff",
    stroke_color: str = "#1A1A1B",  # Trava Black
    group_ids: List[str] = None,
    link: Optional[str] = None
) -> Dict[str, Any]:
    """Create an Excalidraw rectangle element"""
    # Validate the link before adding it
    validated_link = sanitize_url(link) if link else None

    return {
        "id": _generate_id(),
        "type": "rectangle",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": stroke_color,
        "backgroundColor": fill_color,
        "fillStyle": "solid",
        "strokeWidth": 2,  # Thicker border
        "strokeStyle": "solid",
        "roughness": 0,  # Sharp
        "opacity": 100,
        "groupIds": group_ids or [],
        "frameId": None,
        "roundness": None,  # Sharp corners
        "seed": hash(f"{x}{y}") % 1000000,
        "version": 1,
        "versionNonce": hash(f"{x}{y}{width}") % 1000000,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": validated_link,
        "locked": False,
        "customData": {"agentPlaced": True}
    }


def _create_text(
    x: float,
    y: float,
    text: str,
    width: float,
    font_size: int = FONT_SIZE,
    text_align: str = "left",
    group_ids: List[str] = None
) -> Dict[str, Any]:
    """Create an Excalidraw text element"""
    # Calculate height based on text wrapping
    height = estimate_text_height(text, width, font_size)

    return {
        "id": _generate_id(),
        "type": "text",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": "#1A1A1B",  # Trava Black
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": group_ids or [],
        "frameId": None,
        "roundness": None,
        "seed": hash(text) % 1000000,
        "version": 1,
        "versionNonce": hash(f"{text}{x}") % 1000000,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
        "text": text,
        "fontSize": font_size,
        "fontFamily": 2,  # Normal (Inter)
        "textAlign": text_align,
        "verticalAlign": "top",
        "containerId": None,
        "originalText": text,
        "autoResize": True,
        "lineHeight": LINE_HEIGHT,
        "customData": {"agentPlaced": True}
    }


def _create_image(
    x: float,
    y: float,
    width: float,
    height: float,
    file_id: str,
    group_ids: List[str] = None
) -> Dict[str, Any]:
    """Create an Excalidraw image element"""
    return {
        "id": _generate_id(),
        "type": "image",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": "transparent",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": group_ids or [],
        "frameId": None,
        "roundness": None,
        "seed": hash(file_id) % 1000000,
        "version": 1,
        "versionNonce": hash(f"{file_id}{x}") % 1000000,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
        "fileId": file_id,
        "scale": [1, 1],
        "status": "saved",
        "customData": {"agentPlaced": True}
    }


# ================================================
# Helper Functions
# ================================================

def estimate_text_height(text: str, width: float, font_size: int = FONT_SIZE) -> float:
    """
    Estimate the pixel height of wrapped text

    Args:
        text: The text content
        width: Available width for text
        font_size: Font size in pixels

    Returns:
        Estimated height in pixels
    """
    if not text:
        return font_size * LINE_HEIGHT

    # Calculate characters per line
    chars_per_line = max(1, int(width / CHAR_WIDTH))

    # Count lines (including explicit newlines)
    lines = 0
    for paragraph in text.split('\n'):
        if not paragraph:
            lines += 1
        else:
            lines += max(1, (len(paragraph) + chars_per_line - 1) // chars_per_line)

    return lines * font_size * LINE_HEIGHT


async def create_card_group(
    x: float,
    y: float,
    title: str,
    subtitle: str = "",
    description: str = "",
    price_text: str = "",
    card_type: str = "default",
    image_url: Optional[str] = None,
    column_width: int = 300,
    image_height: int = 150,
    fallback_search: Optional[str] = None,
    booking_url: Optional[str] = None
) -> tuple[List[Dict[str, Any]], Dict[str, Any], float]:
    """
    Create a card group containing Rectangle + Text + optional Image

    Args:
        x: X position of the card
        y: Y position of the card
        title: Main title text
        subtitle: Secondary text (e.g., location, date)
        description: Optional longer description
        price_text: Price display text (e.g., "$150/night")
        card_type: Type for color coding (stay, activity, food, etc.)
        image_url: Optional image URL
        column_width: Width of the card
        image_height: Height for images
        fallback_search: Search term for a Tavily image lookup
        booking_url: Optional URL for booking (clicking card opens this link)

    Returns:
        Tuple of (elements list, files dict, card height)
    """
    group_id = _generate_id()
    elements = []
    files = {}

    # Color scheme based on card type (Trava Palette)
    colors = {
        "stay": "#E6FAF5",      # Trava Teal Light
        "activity": "#FFF0E0",  # Adventure Orange Light
        "food": "#FFF0E0",      # Food shares Activity Color
        "sightseeing": "#E6FAF5",  # Sightseeing shares Stay Color
        "flight": "#FFFFFF",    # White
        "default": "#FFFFFF"    # White
    }
    fill_color = colors.get(card_type, colors["default"])

    content_width = column_width - (PADDING * 2)
    current_y = y + PADDING

    # Calculate max characters per line based on content width and font size
    # Different font sizes need different char limits
    def get_max_chars(font_size: int) -> int:
        # Larger fonts = fewer chars per line
        char_width = CHAR_WIDTH * (font_size / 14)  # Scale based on 14px baseline
        return max(20, int(content_width / char_width))

    # Get best image URL: prefer Tavily (reliable CDNs) over scraper URLs (often blocked)
    actual_image_url = None
    if fallback_search:
        logger.info(f"Searching image for: {fallback_search}")
        actual_image_url = await search_tavily_image(fallback_search)
        if actual_image_url:
            logger.info(f"Got Tavily image: {actual_image_url[:60]}...")
    # Fall back to scraper URL if Tavily found nothing
    if not actual_image_url and image_url:
        actual_image_url = image_url
        logger.info(f"Using scraper image: {actual_image_url[:60]}...")

    # Debug: Log the image URL being used
    if actual_image_url:
        logger.info(f"Card '{title}' using image: {actual_image_url[:80]}...")

    # Image (if provided or fallback)
    if actual_image_url:
        file_id = _generate_id()
        img_element = _create_image(
            x + PADDING,
            current_y,
            content_width,
            image_height,
            file_id,
            [group_id]
        )
        elements.append(img_element)

        # Store URL in files dict (frontend will handle loading)
        files[file_id] = {
            "id": file_id,
            "mimeType": "image/png",
            "dataURL": actual_image_url,  # Store URL here for proxy loading
            "created": 1
        }
        current_y += image_height + PADDING

    # Title (wrap if needed)
    wrapped_title = wrap_text(title, get_max_chars(20))
    title_element = _create_text(
        x + PADDING,
        current_y,
        wrapped_title,
        content_width,
        font_size=20,
        group_ids=[group_id]
    )
    elements.append(title_element)
    current_y += estimate_text_height(wrapped_title, content_width, 20) + 8

    # Price (displayed prominently if available)
    if price_text:
        wrapped_price = wrap_text(price_text, get_max_chars(18))
        price_element = _create_text(
            x + PADDING,
            current_y,
            wrapped_price,
            content_width,
            font_size=18,
            group_ids=[group_id]
        )
        elements.append(price_element)
        current_y += estimate_text_height(wrapped_price, content_width, 18) + 8

    # Subtitle (wrap if needed)
    if subtitle:
        wrapped_subtitle = wrap_text(subtitle, get_max_chars(14))
        subtitle_element = _create_text(
            x + PADDING,
            current_y,
            wrapped_subtitle,
            content_width,
            font_size=14,
            group_ids=[group_id]
        )
        elements.append(subtitle_element)
        current_y += estimate_text_height(wrapped_subtitle, content_width, 14) + 8

    # Description (wrap if needed)
    if description:
        wrapped_desc = wrap_text(description, get_max_chars(14))
        desc_element = _create_text(
            x + PADDING,
            current_y,
            wrapped_desc,
            content_width,
            font_size=14,
            group_ids=[group_id]
        )
        elements.append(desc_element)
        current_y += estimate_text_height(wrapped_desc, content_width, 14)

    # Calculate total card height
    card_height = current_y - y + PADDING

    # Background rectangle (added first so it's behind text)
    # If booking_url is provided, clicking the card will open the link
    bg_rect = _create_rectangle(
        x, y,
        column_width,
        card_height,
        fill_color=fill_color,
        group_ids=[group_id],
        link=booking_url
    )
    elements.insert(0, bg_rect)

    return elements, files, card_height


# ================================================
# Masonry Layout Algorithm
# ================================================

async def generate_card_elements(
    items: List[Dict[str, Any]],
    existing_elements: List[Dict[str, Any]],
    viewport_width: int = DEFAULT_VIEWPORT_WIDTH,
) -> tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """
    Generate Excalidraw elements for new items, positioned below existing content.

    Items with a 'day' field are grouped under day-section headers (Day 1, Day 2…).
    Items without a 'day' field fall into an 'Unscheduled' section (or no header at all
    if every item lacks a day, for backwards compatibility).

    Args:
        items: List of dicts with keys: name, type, price, rating, review_count,
               distance, url/bookingUrl, image_url/imageUrl.
               Optional: day (int), date (str "YYYY-MM-DD")
        existing_elements: Current canvas elements (to calculate positioning)
        viewport_width: Canvas width for layout

    Returns:
        new_elements: Elements to APPEND to canvas
        new_files: Files dict to MERGE into canvas files
        group_ids: Group ID for each card (for board_items tracking), in input order
    """
    from datetime import datetime as _dt

    layout = calculate_layout_params(viewport_width)
    column_width = layout['column_width']
    gap = layout['gap']
    image_height = layout['image_height']

    # Find the max_y of existing elements (bottom of existing content)
    max_y = 0.0
    for el in existing_elements:
        if el.get("isDeleted"):
            continue
        el_bottom = el.get("y", 0) + el.get("height", 0)
        if el_bottom > max_y:
            max_y = el_bottom

    start_y = max_y + (gap * 2 if max_y > 0 else 0)
    current_y = start_y

    # Group items by day, preserving original indices for ordered group_ids output
    day_item_indices: Dict[Any, List[int]] = {}
    for i, item in enumerate(items):
        day = item.get("day")  # int or None
        if day not in day_item_indices:
            day_item_indices[day] = []
        day_item_indices[day].append(i)

    # Numbered days first (ascending), then None (unscheduled) last
    sorted_days = sorted(day_item_indices.keys(), key=lambda d: (d is None, d or 0))

    # Only show section headers when at least one item carries day info
    has_day_info = any(d is not None for d in sorted_days)

    all_elements: List[Dict[str, Any]] = []
    all_files: Dict[str, Any] = {}
    group_ids_map: Dict[int, str] = {}  # item index -> excalidraw group_id

    # ── Layout: each day is a column (left-to-right), cards stack vertically ──
    for day_col, day in enumerate(sorted_days):
        indices = day_item_indices[day]
        col_x = gap + day_col * (column_width + gap)
        col_y = current_y

        # ── Day-section header ──────────────────────────────────────────────
        if has_day_info:
            if day is not None:
                first_date = next(
                    (items[i].get("date") for i in indices if items[i].get("date")),
                    None,
                )
                if first_date:
                    try:
                        d = _dt.strptime(first_date, "%Y-%m-%d")
                        header_text = f"Day {day}  ·  {d.strftime('%A, %b %d')}"
                    except Exception:
                        header_text = f"Day {day}"
                else:
                    header_text = f"Day {day}"
            else:
                header_text = "Unscheduled"

            header_el = _create_text(
                col_x,
                col_y,
                header_text,
                column_width,
                font_size=24,
                group_ids=[],
            )
            all_elements.append(header_el)
            header_h = estimate_text_height(header_text, column_width, 24)
            col_y += header_h + gap

        # ── Cards stacked vertically within this day column ─────────────────
        for idx in indices:
            item = items[idx]
            name = item.get("name", "Unnamed")
            item_type = item.get("type", "stay")
            price = item.get("price", "")
            rating = item.get("rating", "")
            review_count = item.get("review_count", item.get("reviewCount", ""))
            distance = item.get("distance", "")
            description = item.get("description", "")
            image_url = item.get("image_url", item.get("imageUrl", ""))
            booking_url = item.get("booking_url", item.get("bookingUrl", item.get("url", "")))

            subtitle_parts = []
            if rating:
                subtitle_parts.append(f"⭐ {rating}")
            if review_count:
                subtitle_parts.append(f"({review_count} reviews)")
            if distance:
                subtitle_parts.append(f"📍 {distance}")
            subtitle = " ".join(subtitle_parts)

            price_text = f"💰 {price}" if price else ""

            card_elements, card_files, height = await create_card_group(
                x=col_x,
                y=col_y,
                title=name,
                subtitle=subtitle,
                description=description,
                price_text=price_text,
                card_type=item_type,
                image_url=image_url if image_url else None,
                column_width=column_width,
                image_height=image_height,
                fallback_search=f"{name} hotel" if item_type == "stay" else name,
                booking_url=booking_url if booking_url else None,
            )

            card_group_id = card_elements[0]["groupIds"][0] if card_elements else _generate_id()
            group_ids_map[idx] = card_group_id

            all_elements.extend(card_elements)
            all_files.update(card_files)

            col_y += height + gap

    # Return group_ids in original input order
    group_ids = [group_ids_map.get(i, _generate_id()) for i in range(len(items))]

    logger.info(f"generate_card_elements: {len(items)} items -> {len(all_elements)} elements, {len(all_files)} files")

    return all_elements, all_files, group_ids
