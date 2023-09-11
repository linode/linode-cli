import argparse
import xml.etree.ElementTree as ET

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Modify XML with workflow information')
parser.add_argument('--workflow-id', required=True)
parser.add_argument('--workflow-run-number', required=True)
parser.add_argument('--repository', required=True)
parser.add_argument('--head-branch', required=True)
parser.add_argument('--commit-sha', required=True)

args = parser.parse_args()

# Open and parse the XML file
xml_file_path = 'your_xml_report.xml'  # Replace with your XML file path
tree = ET.parse(xml_file_path)
root = tree.getroot()

# Create new elements for the information
workflow_id_element = ET.Element('workflow_id')
workflow_id_element.text = args.workflow_id

workflow_run_number_element = ET.Element('workflow_run_number')
workflow_run_number_element.text = args.workflow_run_number

repository_element = ET.Element('repository')
repository_element.text = args.repository

head_branch_element = ET.Element('head_branch')
head_branch_element.text = args.head_branch

commit_sha_element = ET.Element('commit_sha')
commit_sha_element.text = args.commit_sha

# Add the new elements to the root of the XML
root.append(workflow_id_element)
root.append(workflow_run_number_element)
root.append(repository_element)
root.append(head_branch_element)
root.append(commit_sha_element)

# Save the modified XML
modified_xml_file_path = 'modified_xml_report.xml'  # Replace with the desired output path
tree.write(modified_xml_file_path)

print(f'Modified XML saved to {modified_xml_file_path}')