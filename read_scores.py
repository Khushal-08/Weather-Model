import json
try:
    with open('lighthouse_report.report.json', encoding='utf-8') as f:
        d = json.load(f)
        for cat in ['performance', 'accessibility', 'best-practices', 'seo']:
            score = d['categories'].get(cat, {}).get('score')
            if score is not None:
                print(f"{cat}: {score*100}")
            else:
                print(f"{cat}: None")
except Exception as e:
    print(e)
