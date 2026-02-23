"""
Template trip boards for TRAVA
"""

from typing import Dict, List, Any
import uuid


def generate_welcome_template() -> Dict[str, Any]:
    """
    Generate a welcome template with introduction and guide for new trips.
    Returns a dict with elements and files for Excalidraw.
    """

    # Helper to create consistent IDs
    def gen_id():
        return str(uuid.uuid4())

    elements: List[Dict[str, Any]] = []

    # Title: "Welcome to TRAVA! 🗺️"
    elements.append({
        "id": gen_id(),
        "type": "text",
        "x": 100,
        "y": 100,
        "width": 600,
        "height": 70,
        "fontSize": 48,
        "fontFamily": 2,  # Normal (Inter)
        "text": "Welcome to TRAVA! 🗺️",
        "textAlign": "center",
        "verticalAlign": "top",
        "baseline": 58,
        "containerId": None,
        "originalText": "Welcome to TRAVA! 🗺️",
        "lineHeight": 1.25,
        "strokeColor": "#1A1A1B",  # Trava Black
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 0,  # Sharp
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": 12345,
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False
    })

    # Box: What is TRAVA?
    box1_id = gen_id()
    text1_id = gen_id()
    elements.append({
        "id": box1_id,
        "type": "rectangle",
        "x": 100,
        "y": 200,
        "width": 650,
        "height": 200,
        "strokeColor": "#1A1A1B",  # Trava Black
        "backgroundColor": "#FFFFFF",  # White
        "fillStyle": "solid",
        "strokeWidth": 3,  # Brutalist Thick Border
        "strokeStyle": "solid",
        "roughness": 0,  # Sharp
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,  # Sharp corners
        "seed": 12346,
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "boundElements": [{"type": "text", "id": text1_id}],
        "updated": 1,
        "link": None,
        "locked": False
    })

    elements.append({
        "id": text1_id,
        "type": "text",
        "x": 120,
        "y": 220,
        "width": 610,
        "height": 160,
        "fontSize": 20,
        "fontFamily": 2,  # Normal (Inter)
        "text": "✈️ What is TRAVA?\n\nTRAVA is your AI-powered travel planning assistant.\nChat with TRAVA to create personalized trip boards with\nflights, hotels, activities, and itineraries - all visualized\non an interactive canvas!",
        "textAlign": "left",
        "verticalAlign": "top",
        "baseline": 18,
        "containerId": box1_id,
        "originalText": "✈️ What is TRAVA?\n\nTRAVA is your AI-powered travel planning assistant.\nChat with TRAVA to create personalized trip boards with\nflights, hotels, activities, and itineraries - all visualized\non an interactive canvas!",
        "lineHeight": 1.25,
        "strokeColor": "#1A1A1B",  # Trava Black
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": 12347,
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False
    })

    # Box: How to Use TRAVA
    box2_id = gen_id()
    text2_id = gen_id()
    elements.append({
        "id": box2_id,
        "type": "rectangle",
        "x": 100,
        "y": 450,
        "width": 650,
        "height": 280,
        "strokeColor": "#1A1A1B",  # Trava Black
        "backgroundColor": "#FFFFFF",  # White
        "fillStyle": "solid",
        "strokeWidth": 3,  # Brutalist Thick Border
        "strokeStyle": "solid",
        "roughness": 0,  # Sharp
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,  # Sharp corners
        "seed": 12348,
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "boundElements": [{"type": "text", "id": text2_id}],
        "updated": 1,
        "link": None,
        "locked": False
    })

    elements.append({
        "id": text2_id,
        "type": "text",
        "x": 120,
        "y": 470,
        "width": 610,
        "height": 240,
        "fontSize": 20,
        "fontFamily": 2,  # Normal (Inter)
        "text": "🎯 How to Use TRAVA:\n\n1. Use the chat on the left to talk to TRAVA\n2. Describe your travel plans and preferences\n3. Say \"Create Board\" to generate your trip\n4. TRAVA will add flights, hotels, and activities\n   to this canvas\n5. Click and drag elements to organize your board\n6. Edit, add notes, or draw connections as needed",
        "textAlign": "left",
        "verticalAlign": "top",
        "baseline": 18,
        "containerId": box2_id,
        "originalText": "🎯 How to Use TRAVA:\n\n1. Use the chat on the left to talk to TRAVA\n2. Describe your travel plans and preferences\n3. Say \"Create Board\" to generate your trip\n4. TRAVA will add flights, hotels, and activities\n   to this canvas\n5. Click and drag elements to organize your board\n6. Edit, add notes, or draw connections as needed",
        "lineHeight": 1.25,
        "strokeColor": "#1A1A1B",  # Trava Black
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": 12349,
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False
    })

    # Box: What TRAVA Needs
    box3_id = gen_id()
    text3_id = gen_id()
    elements.append({
        "id": box3_id,
        "type": "rectangle",
        "x": 100,
        "y": 780,
        "width": 650,
        "height": 200,
        "strokeColor": "#1A1A1B",  # Trava Black
        "backgroundColor": "#FFFFFF",  # White
        "fillStyle": "solid",
        "strokeWidth": 3,  # Brutalist Thick Border
        "strokeStyle": "solid",
        "roughness": 0,  # Sharp
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,  # Sharp corners
        "seed": 12350,
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "boundElements": [{"type": "text", "id": text3_id}],
        "updated": 1,
        "link": None,
        "locked": False
    })

    elements.append({
        "id": text3_id,
        "type": "text",
        "x": 120,
        "y": 800,
        "width": 610,
        "height": 160,
        "fontSize": 20,
        "fontFamily": 2,  # Normal (Inter)
        "text": "📋 What TRAVA Needs to Create Your Trip:\n\n📍 Destination (city/country)\n📅 Travel dates (or approximate timeframe)\n💰 Budget range (optional but helpful)\n🎨 Preferences (activities, food, accommodation style)",
        "textAlign": "left",
        "verticalAlign": "top",
        "baseline": 18,
        "containerId": box3_id,
        "originalText": "📋 What TRAVA Needs to Create Your Trip:\n\n📍 Destination (city/country)\n📅 Travel dates (or approximate timeframe)\n💰 Budget range (optional but helpful)\n🎨 Preferences (activities, food, accommodation style)",
        "lineHeight": 1.25,
        "strokeColor": "#1A1A1B",  # Trava Black
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": 12351,
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False
    })


    return {
        "elements": elements,
        "files": {}
    }
