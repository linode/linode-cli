import argparse
import xml.etree.ElementTree as ET
import requests

latest_release_url = "https://api.github.com/repos/linode/linode-cli/releases/latest"


def get_release_version():
    url = latest_release_url

    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors

        release_info = response.json()
        version = release_info["tag_name"]

        # Remove 'v' prefix if it exists
        if version.startswith("v"):
            version = version[1:]

        return str(version)

    except requests.exceptions.RequestException as e:
        print("Error:", e)
    except KeyError:
        print("Error: Unable to fetch release information from GitHub API.")


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Modify XML with workflow information')
parser.add_argument('--branch_name', required=True)
parser.add_argument('--gha_run_id', required=True)
parser.add_argument('--gha_run_number', required=True)
parser.add_argument('--release_tag', required=False)
parser.add_argument('--xmlfile', required=True)  # Added argument for XML file path

args = parser.parse_args()

# Open and parse the XML file
xml_file_path = args.xmlfile
tree = ET.parse(xml_file_path)
root = tree.getroot()

# Create new elements for the information
branch_name_element = ET.Element('branch_name')
branch_name_element.text = args.branch_name

gha_run_id_element = ET.Element('gha_run_id')
gha_run_id_element.text = args.gha_run_id

gha_run_number_element = ET.Element('gha_run_number')
gha_run_number_element.text = args.gha_run_number

gha_release_tag_element = ET.Element('release_tag')
gha_release_tag_element.text = get_release_version()

# Add the new elements to the root of the XML
root.append(branch_name_element)
root.append(gha_run_id_element)
root.append(gha_run_number_element)
root.append(gha_release_tag_element)

# Save the modified XML
modified_xml_file_path = xml_file_path  # Overwrite it
tree.write(modified_xml_file_path)

print(f'Modified XML saved to {modified_xml_file_path}')
