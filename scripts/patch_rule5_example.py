"""Patch judge rule 5 to add critical application note for n (X%) pattern."""
path = r'D:\revisto_evidence_aligned_clean\new_pipeline\prompts\judge_prompt.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

OLD = ('   These are universal typographic conventions in medical publishing (Lancet, NEJM, JAMA), NOT different values. '
       'Cite the full expression as evidence_text. This does NOT permit mismatched numbers: `(six [5%])` does NOT substantiate "6%".')

NEW = (OLD + '\n'
       '   **CRITICAL APPLICATION — count vs percentage:** When a passage says `"35 (32%) participants had infections"`, '
       'the number `35` is the event count (n) and `32%` is the percentage. '
       'A claim stating `"infections occurred in 32% of patients"` IS a verbatim match — cite `"35 (32%) participants had infections"` as evidence_text. '
       'Similarly `"37 (34%) participants in the placebo group had infections"` is a verbatim match for `"34% of placebo-treated patients"`. '
       'Do NOT confuse the count (35, 37) with the percentage (32%, 34%). The percentage is ALWAYS the value inside the parentheses.')

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('DONE — critical application note added')
else:
    print('NOT FOUND')
    # Show line 33 area
    lines = content.split('\n')
    for i, l in enumerate(lines[27:36], 28):
        print(f'{i}: {repr(l[:100])}')
