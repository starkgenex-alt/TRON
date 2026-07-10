import json

transcript_path = r'c:\Users\HP\AppData\Roaming\Code\User\workspaceStorage\1ed0ab594125a2462c28d9a65d3c4049\GitHub.copilot-chat\transcripts\a0665eda-6b90-4432-9acd-fdadb2b7e48c.jsonl'

with open(transcript_path, encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Search for messages with HTML dashboard code
found_count = 0
for i, line in enumerate(reversed(lines)):
    if found_count >= 2:
        break
    try:
        msg = json.loads(line)
        text = msg.get('message', '')
        
        # Look for HTML dashboard sections with CSS
        if ('<style>' in text or '<html>' in text) and ('dashboard' in text.lower() or 'streamlit' in text.lower()):
            print(f"\n{'='*80}")
            print(f"Found dashboard code (line {len(lines)-i}):")
            print(f"{'='*80}\n")
            # Print more content
            print(text[:5000])
            found_count += 1
    except:
        pass

print("\nSearch complete.")
