import json, re, glob, os
from html.parser import HTMLParser

class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
    def handle_data(self, d):
        self.result.append(d)
    def get_text(self):
        return ''.join(self.result)

def get_snippet(description, title=None):
    if not description:
        return None
    text = str(description)

    if re.search(r'<[a-z][\s\S]*>', text, re.IGNORECASE):
        text = re.sub(r'<\s*br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/p\s*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*li\s*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/li\s*>', '\n', text, flags=re.IGNORECASE)
        s = HTMLStripper()
        s.feed(text)
        text = s.get_text()

    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'\\([*_\[\](){}+#>|`~])', r'\1', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'[\t\r]+', ' ', text)
    text = re.sub(r' {2,}', ' ', text)

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    label_prefix = re.compile(r'^\w+(\s+\w+){0,2}\s*:\s*')
    cta_prefix = re.compile(r'^(back to|buy|register|sign up|rsvp|tickets?|click|tap|view|see all|read more|get|call or text|call or email)\b', re.IGNORECASE)
    bad_anywhere = re.compile(r'\b(zoom|meeting id|passcode|one tap|meeting url|webex|microsoft teams|google meet|agenda|packet|minutes|prohibited|not permitted|are not allowed)\b', re.IGNORECASE)
    money_or_price = re.compile(r'(\$\s*\d|\bprice\b|\bfee\b|\badmission\b|\bfree but\b)', re.IGNORECASE)

    norm_title = re.sub(r'[^a-z0-9]+', ' ', title.lower()).strip() if title else None
    def norm_text(s):
        return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

    def salvage_label(line):
        if not label_prefix.match(line):
            return line
        rest = label_prefix.sub('', line).strip()
        if len(rest) < 30:
            return ''
        if not re.search(r'\b(the|a|an|and|or|for|with|to|from|at|in|on|by|is|are|was|will|this|that)\b', rest, re.IGNORECASE):
            return ''
        if label_prefix.match(rest):
            return ''
        return rest

    def score_line(line):
        if len(line) < 15:
            return -999, line
        line = salvage_label(line)
        if not line:
            return -999, ''
        if cta_prefix.match(line):
            return -999, line
        if bad_anywhere.search(line):
            return -999, line

        score = 0
        if re.search(r'[.!?]', line): score += 3
        if re.search(r'\b(the|a|an|and|or|but|for|with|to|from|at|in|on|by)\b', line, re.IGNORECASE): score += 2
        if re.search(r'\b(join|learn|discover|explore|enjoy|experience|celebrate|meet|hear|watch|featuring|presents)\b', line, re.IGNORECASE): score += 2
        if money_or_price.search(line): score -= 3
        digit_count = len(re.findall(r'\d', line))
        if digit_count >= 6: score -= 3
        if re.search(r'\b(from almost anywhere in the world|from anywhere in the world)\b', line, re.IGNORECASE): score -= 5
        if len(line) < 25 and not re.search(r'[.!?]', line): score -= 3
        if not re.search(r'\b(the|a|an|is|are|was|will|has|have|can|do|and|but|for|with|from)\b', line, re.IGNORECASE) and len(line) < 40: score -= 3
        if norm_title:
            nt = norm_text(line)
            if nt == norm_title: score -= 6
            elif norm_title in nt and len(nt) - len(norm_title) < 15: score -= 4
        if len(line) >= 40: score += 1
        if len(line) > 220: score -= 2
        return score, line

    best = None
    best_score = -999
    for raw_line in lines:
        parts = re.split(r'(?<=[.!?])\s+', raw_line)
        for part in parts:
            part = part.strip()
            if not part: continue
            s, processed = score_line(part)
            if s > best_score:
                best_score = s
                best = processed

    if not best or best_score < 0:
        return None

    if len(best) <= 100:
        return best
    cut = best.rfind(' ', 0, 100)
    if cut < 40: cut = 100
    return re.sub(r'[\s(,\-;:]+$', '', best[:cut]) + '...'


# Check specific problem cases
problem_titles = [
    'Board of Public Works Meeting',
    'Metropolitan Planning Organization Citizens Advisory Committee',
    'Bookmobile to Ballybunion',
    'Symphonic Band',
    'Gallery Tour',
    'JOHN MCENROE: IN THE REALM OF PERFECTION',
    'EYES WITHOUT A FACE',
    'IU Latin Jazz Ensemble',
    'Harmony and Power',
    'The Game | Hoosiers on Screen',
    'Doctoral Recital',
    'Free but ticketed',
]

base = '/Users/jonudell/community-calendar/cities'
print("=== CHECKING SPECIFIC PROBLEM CASES ===\n")
for city_dir in sorted(glob.glob(os.path.join(base, '*/events.json'))):
    city = os.path.basename(os.path.dirname(city_dir))
    with open(city_dir) as f:
        events = json.load(f)
    for e in events:
        t = e.get('title', '')
        for prob in problem_titles:
            if prob.lower() in t.lower():
                snippet = get_snippet(e.get('description', ''), t)
                print(f"[{city}] {t}")
                print(f"  -> {snippet or '(no snippet)'}\n")
                break

# Now generate full report
out = []
out.append('# Snippet Report (v3 — improved scoring)\n')
totals = {'with': 0, 'without': 0}

for city_dir in sorted(glob.glob(os.path.join(base, '*/events.json'))):
    city = os.path.basename(os.path.dirname(city_dir))
    with open(city_dir) as f:
        events = json.load(f)

    with_snippet = 0
    without_snippet = 0
    snippet_lines = []
    no_snippet_lines = []

    for e in events:
        snippet = get_snippet(e.get('description', ''), e.get('title', ''))
        title = e.get('title', '(no title)')
        if snippet:
            with_snippet += 1
            snippet_lines.append(f'- **{title}** \u2014 {snippet}')
        else:
            without_snippet += 1
            desc = (e.get('description', '') or '')[:120].replace('\n', ' ').replace('\u2028', ' ').replace('\u2029', ' ')
            if desc:
                no_snippet_lines.append(f'- **{title}** \u2014 `{desc}`')
            else:
                no_snippet_lines.append(f'- **{title}** \u2014 *(no description)*')

    totals['with'] += with_snippet
    totals['without'] += without_snippet
    pct = round(100 * with_snippet / len(events)) if events else 0

    out.append(f'## {city.title()} ({len(events)} events, {pct}% have snippets)\n')
    out.append(f'### With snippets ({with_snippet})\n')
    for line in snippet_lines:
        out.append(line)
    out.append(f'\n### Without snippets ({without_snippet})\n')
    for line in no_snippet_lines:
        out.append(line)
    out.append('')

total_events = totals['with'] + totals['without']
pct = round(100 * totals['with'] / total_events) if total_events else 0
out.insert(1, f'**Total: {total_events} events, {totals["with"]} with snippets ({pct}%), {totals["without"]} without**\n')

content = '\n'.join(out)
content = content.replace('\u2028', ' ').replace('\u2029', ' ')
with open('/Users/jonudell/community-calendar/docs/snippet-report.md', 'w') as f:
    f.write(content)

print(f"\nWritten to docs/snippet-report.md")
print(f"Total: {total_events} events, {totals['with']} with snippets ({pct}%), {totals['without']} without")
