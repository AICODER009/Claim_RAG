# Issue Investigation & Action Plan

## Root Cause Analysis for Each Failure

### CT-301 (Safety AE rates) - BLOCK 29%
**Data EXISTS in Qdrant** (chunk_19 has "urinary tract infection (10%...)")
but retriever ranked it at position 6+ instead of top 5.

**Root cause:** chunk_28 and chunk_19 both have the UTI data but they're
ranked below chunks about contraindications and general safety info.
The dense embedding for "adverse reactions >= 5%" is too generic - it matches
many safety-related chunks rather than the specific AE percentage table.

**FIX: Increase top-K from 5 to 10 for judge.** The data is there, just not
in the top 5. Alternatively, search for EXACT numbers from the claim.

---

### CT-307 (ISI block) - BLOCK 50%
**Partially available.** 7/12 sub-assertions found.
Missing: infection risk, AE rates, pregnancy, breastfeeding sections.
These are in different PI sections that aren't in the top 5.

**Root cause:** Same as CT-301. The claim is too long (12 sub-assertions).
5 passages from a single PI can't cover 12 different sections.

**FIX: Either (a) split long ISI claims into sub-claims before processing,
or (b) increase top-K to 15 for claims with > 200 chars.**

---

### CT-603 (Injection timing) - BLOCK 20%
**Data EXISTS:** chunk_10 has "30 to 90 seconds", chunk_16 has "30 to 90 seconds"
But the claim says "~30-90 second" and the PI says "30 to 90 seconds".

**Root cause:** The retriever found VYVGART passages (competitor exclusion worked!)
but the specific injection timing chunk (chunk_10, chunk_16) ranked outside top 5.
The dense embedding for "injection time monitoring" is too generic.

**FIX:** Same top-K increase would help. Also the claim references "prefilled
syringe" and "single dose vial" which are in chunk_8 and chunk_10 respectively.

---

### CT-311 (Breastfeeding) - SOFT_FLAG 67%
**REGRESSION from v1.** "breastfed infants" returns 0 results from MatchText!
The PI chunk uses different wording than the claim.

**Root cause:** The retrieved passages DO cover lactation risk assessment
(Passage 1 is the Risk Summary section). But the judge found 2/3 sub-assertions
covered and marked "may cause serious adverse reactions in breastfed infants"
as NOT covered because that exact phrase isn't in the passages.

**FIX:** This is actually CORRECT behavior - the judge is being strict.
The PI says "no information regarding presence... in human milk" which is
different from "may cause serious adverse reactions in breastfed infants."
This is a genuine substantiation gap, not a retrieval problem.

---

### CT-601 (Dosing) - BLOCK 29%
**Data EXISTS but DIFFERENT:** The claim says "2000 mg/20 mL vial"
but the PI says "1,000 mg/5 mL" (200 mg/2,000 units per mL).
chunk_17: "1,000 mg efgartigimod alfa and 10,000 units hyaluronidase per 5 mL"

**Root cause:** The claim text itself may be WRONG or from a different
formulation version. The PI describes:
- PFS: 1,000 mg / 10 mL
- Vial: 1,000 mg / 5 mL
Neither matches "2000 mg/20 mL" from the claim.

**FIX:** This is a legitimate BLOCK. The claim contains numbers that
don't match the PI. The judge correctly flagged it.

---

## Summary: What's Real vs What's Fixable

| Issue | Root Cause | Fixable Now? |
|-------|-----------|-------------|
| CT-301 (29%) | Data exists but ranked 6+ | YES - increase top-K |
| CT-307 (50%) | ISI too complex for top-5 | YES - increase top-K or split claims |
| CT-603 (20%) | Injection timing chunk ranked low | YES - increase top-K |
| CT-311 (67%) | Genuine substantiation gap | NO - correct behavior |
| CT-601 (29%) | Claim numbers don't match PI | NO - correct behavior |

## IMMEDIATE FIX: Increase Top-K

Change judge passages from top 5 to top 10 for ALL claims.
This will fix CT-301, CT-307, and CT-603 since the data EXISTS
in the corpus, it's just ranked outside the top 5 window.
