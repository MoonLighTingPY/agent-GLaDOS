import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glados.inventory.storage import InventoryDB

def setup_demo_inventory():
    """Add some demo items to the inventory for testing."""
    db = InventoryDB()
    
    # Electronics
    db.upsert_item("buck converter", "shelf A2, electronics section", {"type": "voltage regulator", "voltage": "12V to 5V"})
    db.upsert_item("green board", "shelf A2, electronics section", {"type": "voltage regulator", "voltage": "12V to 5V"})
    db.upsert_item("arduino uno", "drawer B1, microcontrollers", {"type": "development board", "pins": 14})
    db.upsert_item("raspberry pi 4", "drawer B2, single board computers", {"type": "SBC", "ram": "4GB"})
    db.upsert_item("breadboard", "drawer C1, prototyping", {"type": "solderless breadboard", "holes": 830})
    
    # Tools
    db.upsert_item("soldering iron", "workbench, left side", {"type": "tool", "temp": "350°C"})
    db.upsert_item("multimeter", "workbench, drawer 2", {"type": "measurement", "brand": "fluke"})
    db.upsert_item("oscilloscope", "shelf D1, instruments", {"type": "measurement", "channels": 4})
    
    # Components
    db.upsert_item("resistors", "component box 1, shelf E", {"type": "passive component", "range": "1Ω to 1MΩ"})
    db.upsert_item("capacitors", "component box 2, shelf E", {"type": "passive component", "range": "1pF to 1000μF"})
    db.upsert_item("leds", "component box 3, shelf E", {"type": "indicator", "colors": "red, green, blue, white"})
    
    print("Demo inventory items added!")
    
    # List all items
    items = db.list_items()
    print(f"\nTotal items: {len(items)}")
    for item in items:
        print(f"- {item['name']}: {item['location']}")

if __name__ == "__main__":
    setup_demo_inventory()
