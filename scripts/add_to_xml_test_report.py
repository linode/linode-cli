import argparse
import xml.etree.ElementTree as ET

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Modify XML with workflow information')
parser.add_argument('--semanticversion', required=True)
parser.add_argument('--xmlfile', required=True)  # Added argument for XML file path

args = parser.parse_args()

# Open and parse the XML file
xml_file_path = args.xmlfile
tree = ET.parse(xml_file_path)
root = tree.getroot()

# Create new elements for the information
semanticversion_element = ET.Element('semanticversion')
semanticversion_element.text = args.semanticversion

# Add the new elements to the root of the XML
root.append(semanticversion_element)

# Save the modified XML
modified_xml_file_path = xml_file_path  # Overwrite it
tree.write(modified_xml_file_path)

print(f'Modified XML saved to {modified_xml_file_path}')
