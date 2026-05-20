"""Update judge prompt rule 5 to add written-word bracket format."""
path = r'D:\revisto_evidence_aligned_clean\new_pipeline\prompts\judge_prompt.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

OLD = ('   **CLINICAL PAPER FORMAT RULE (ICH E3 / CONSORT standard):** All peer-reviewed clinical trial publications report percentages in the format `n (X%)` \u2014 e.g., "35 (32%) participants" or "19 [17%] of 111". This is a universal typographic convention, NOT a different value. If a claim states a percentage (e.g., "32%") and the evidence passage contains that exact percentage within an `n (X%)` expression (e.g., "35 (32%) participants in the subcutaneous efgartigimod PH20 group"), treat this as a VERBATIM MATCH for that percentage. The evidence_text you cite must include the full `n (X%)` expression. This rule applies to ALL clinical publications (Lancet, NEJM, JAMA, etc.) \u2014 it is a formatting normalization, not a content concession. It does NOT permit mismatched numbers: "35 (32%)" does NOT substantiate a claim of "34%".')

NEW = ('   **CLINICAL PAPER FORMAT RULE (ICH E3 / CONSORT standard):** Peer-reviewed clinical publications use several equivalent formats \u2014 all count as verbatim matches for the stated percentage:\n'
       '   - Numeric-parentheses: `35 (32%) participants` \u2192 verbatim match for "32%"\n'
       '   - Numeric-brackets: `19 [17%] of 111` \u2192 verbatim match for "17%"\n'
       '   - Written-word brackets: `(six [5%])` or `(two [1%])` \u2192 verbatim match for "5%" or "1%" (CONSORT style for n<10)\n'
       '   These are universal typographic conventions in medical publishing (Lancet, NEJM, JAMA), NOT different values. Cite the full expression as evidence_text. This does NOT permit mismatched numbers: `(six [5%])` does NOT substantiate "6%".')

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('DONE - written-word format variant added to rule 5')
else:
    print('NOT FOUND')
    # Debug: find line 29
    lines = content.split('\n')
    print(repr(lines[28][:120]))
