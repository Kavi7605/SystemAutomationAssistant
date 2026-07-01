import re
with open('src/core/command_parser.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = re.sub(r'"path":', r'"target_folder":', c)
c = c.replace('The `path` parameter must', 'The `target_folder` parameter must')
with open('src/core/command_parser.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("done")
