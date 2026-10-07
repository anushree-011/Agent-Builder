import json

with open('D:/Agent-Builder/github_fetched_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('D:/Agent-Builder/parsed_summary.txt', 'w', encoding='utf-8') as out:
    out.write("=== KRISHNA-ITTL README ===\n")
    out.write(data.get('readme_ittl', '') + "\n\n")

    out.write("=== KRISH-EXE-29 PROFILE ===\n")
    out.write(json.dumps(data.get('profile_krish', {}), indent=2) + "\n\n")

    out.write("=== KRISH-EXE-29 REPOS ===\n")
    for r in data.get('repos_krish', []):
        out.write(f"Name: {r.get('name')}\n")
        out.write(f"Description: {r.get('description')}\n")
        out.write(f"Language: {r.get('language')}\n")
        out.write(f"Stars: {r.get('stargazers_count')}, Forks: {r.get('forks_count')}\n")
        out.write(f"Fork: {r.get('fork')}\n")
        out.write(f"URL: {r.get('html_url')}\n")
        out.write("-" * 40 + "\n")

    out.write("\n=== KRISH-EXE-29 EXISTING README ===\n")
    out.write(data.get('readme_krish', '') + "\n")

print("Done parsing")
