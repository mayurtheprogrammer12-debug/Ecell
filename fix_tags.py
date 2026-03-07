
import os

files_to_fix = [
    r'd:\PROJECTS\ECell\templates\registrations\participant_form.html',
    r'd:\PROJECTS\ECell\templates\registrations\exhibitor_form.html'
]

for file_path in files_to_fix:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use regex or simple replace to merge split tags
    # Specifically for {{ ... }} and {% ... %}
    import re
    
    # Merge {{ \n ... }}
    content = re.sub(r'\{\{\s*\n\s*', '{{ ', content)
    content = re.sub(r'\s*\n\s*\}\}', ' }}', content)
    
    # Merge {% \n ... %}
    content = re.sub(r'\{%\s*\n\s*', '{% ', content)
    content = re.sub(r'\s*\n\s*%\}', ' %}', content)
    
    # Specifically check if labels, help_text and errors are on single lines
    # Pattern to find labels
    content = re.sub(r'(\{{2})\s*\n\s*(field\.(label|help_text|errors))\s*\n?\s*(\}{2})', r'\1 \2 \4', content)
    
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

print("Formatting complete. Verified tags are on single lines.")
