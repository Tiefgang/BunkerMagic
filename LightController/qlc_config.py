import json
import xml.etree.ElementTree as ET


# Load JSON data
def load_json(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


# Add fixtures to the QLC+ XML file
def add_fixtures(json_data, xml_filename):
    tree = ET.parse(xml_filename)
    root = tree.getroot()
    engine = root.find("Engine")

    if engine is None:
        print("Invalid QLC+ file: No Engine section found.")
        return

    fixtures = engine.find("Fixture")
    if fixtures is None:
        fixtures = ET.SubElement(engine, "Fixture")

    fixture_id = 0  # Assign fixture IDs incrementally
    address = 0  # Start address

    for mac, device in json_data.items():
        ip = device.get("ip", "")
        name = device.get("name", "Unknown") or "Unknown"
        rows = int(device.get("rows", 1))
        cols = int(device.get("columns", 1))
        channels = rows * cols * 3  # Assuming RGB per pixel

        fixture = ET.SubElement(engine, "Fixture")
        ET.SubElement(fixture, "Manufacturer").text = "Generic"
        ET.SubElement(fixture, "Model").text = "RGBPanel"
        ET.SubElement(fixture, "Mode").text = "RGB"
        ET.SubElement(fixture, "Weight").text = "100"
        ET.SubElement(fixture, "Height").text = str(rows)
        ET.SubElement(fixture, "ID").text = str(fixture_id)
        ET.SubElement(fixture, "Name").text = name
        ET.SubElement(fixture, "Universe").text = "0"  # Assign universe dynamically if needed
        ET.SubElement(fixture, "Address").text = str(address)
        ET.SubElement(fixture, "Channels").text = str(channels)

        fixture_id += 1
        address += channels  # Increment address by the number of channels used

    # Save updated XML file
    tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
    print(f"Updated {xml_filename} with new fixtures.")


# Example usage
json_filename = "devices.json"  # Replace with actual JSON file name
xml_filename = "qlcplus_project.qxw"  # Replace with actual QLC+ project file

data = load_json(json_filename)
add_fixtures(data, xml_filename)
