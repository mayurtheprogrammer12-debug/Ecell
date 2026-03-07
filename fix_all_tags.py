
import os
import re

files_to_check = [
    r'd:\PROJECTS\ECell\templates\registrations\participant_form.html',
    r'd:\PROJECTS\ECell\templates\registrations\exhibitor_form.html',
    r'd:\PROJECTS\ECell\templates\registrations\payment.html',
    r'd:\PROJECTS\ECell\templates\registrations\success.html'
]

def fix_split_tags(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for split variable tags {{ \n ... }}
    # We want to catch instances where the opening {{ or closing }} is on a different line from the variable
    # We also want to merge the variable if it's split over multiple lines
    new_content = re.sub(r'\{\{\s*([\s\S]*?)\s*\}\}', lambda m: '{{ ' + ' '.join(m.group(1).split()) + ' }}', content)
    
    # Pattern for split block tags {% \n ... %}
    new_content = re.sub(r'\{%\s*([\s\S]*?)\s*%\}', lambda m: '{% ' + ' '.join(m.group(1).split()) + ' %}', new_content)

    if content != new_content:
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print(f"Fixed split tags in {file_path}")
    else:
        print(f"No split tags found in {file_path}")

for f_path in files_to_check:
    if os.path.exists(f_path):
        fix_split_tags(f_path)
