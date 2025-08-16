import argparse
from .storage import InventoryDB

def main():
    parser = argparse.ArgumentParser(description="Inventory DB CLI")
    sub = parser.add_subparsers(dest="cmd")

    add_p = sub.add_parser("add", help="Add or update item")
    add_p.add_argument("name")
    add_p.add_argument("location")

    list_p = sub.add_parser("list", help="List items")

    find_p = sub.add_parser("find", help="Find item by substring")
    find_p.add_argument("query")

    args = parser.parse_args()
    db = InventoryDB()
    if args.cmd == "add":
        db.upsert_item(args.name, args.location)
        print("Upserted.")
    elif args.cmd == "list":
        for it in db.list_items():
            print(f"{it['name']} -> {it['location']}")
    elif args.cmd == "find":
        it = db.find_item(args.query)
        if it:
            print(f"Found: {it['name']} at {it['location']}")
        else:
            print("Not found")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
