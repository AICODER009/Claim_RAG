# First 50 Claims — Substantiation Results

**Date:** 2026-05-17 01:05
**Total time:** 826s (13.8 min)
**Average per claim:** 16.5s

## Summary

| Verdict | Count | % |
|---------|------:|--:|
| ✅ PASS | 40 | 80% |
| ⚠️ SOFT_FLAG | 2 | 4% |
| ❌ BLOCK | 8 | 16% |
| **Total** | **50** | **100%** |

**Average coverage:** 85%

---

## Detailed Results

### #1 (Row 4) — ✅ PASS (100.0%)

- **CT-ID:** `CT-603` | **Time:** 19.0s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** VYVGART HYTRULO is for use under the skin (subcutaneous) injection only.

- **Search query:** What evidence supports that VYVGART HYTRULO is for subcutaneous injection only?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.046)

**Sub-assertions:**

- ✅ VYVGART HYTRULO is for use under the skin (subcutaneous) injection only
  > *"VYVGART HYTRULO is for subcutaneous use only"*

**Assessment:** Fully substantiated - PI explicitly states VYVGART HYTRULO is for subcutaneous use only, which directly supports the claim about subcutaneous injection only.

---

### #2 (Row 5) — ❌ BLOCK (50.0%)

- **CT-ID:** `CT-603` | **Time:** 21.4s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** You should not inject VYVGART HYTRULO into a vein or muscle.

- **Search query:** What evidence supports that VYVGART HYTRULO should not be injected into a vein or muscle?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.045)

**Sub-assertions:**

- ✅ You should not inject VYVGART HYTRULO into a vein
  > *"VYVGART HYTRULO is for subcutaneous use only. Do not administer intravenously."*
- ❌ You should not inject VYVGART HYTRULO into a muscle

**Assessment:** Partial substantiation - intravenous administration prohibition is explicitly covered, but intramuscular administration prohibition is not found in the evidence.

---

### #3 (Row 6) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 15.0s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not use VYVGART HYTRULO if it is expired.

- **Search query:** What evidence supports avoiding use of VYVGART HYTRULO if it is expired?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.044)

**Sub-assertions:**

- ✅ Do not use VYVGART HYTRULO if it is expired
  > *"Do not use the prefilled syringe if it is expired."*

**Assessment:** Claim is fully substantiated by verbatim instruction in the Prescribing Information regarding not using expired prefilled syringes.

---

### #4 (Row 7) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 17.1s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not use the prefilled syringe if it is cracked, broken, or damaged.

- **Search query:** What evidence supports avoiding use of a prefilled syringe if it is cracked, broken, or damaged?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.049)

**Sub-assertions:**

- ✅ Do not use the prefilled syringe if it is cracked
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*
- ✅ Do not use the prefilled syringe if it is broken
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*
- ✅ Do not use the prefilled syringe if it is damaged
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*

**Assessment:** Claim is fully substantiated with exact verbatim match from the VYVGART HYTRULO Prescribing Information covering all three damage conditions.

---

### #5 (Row 9) — ❌ BLOCK (50.0%)

- **CT-ID:** `CT-604` | **Time:** 18.3s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** A novel treatment for adult patients with chronic inflammatory demyelinating polyneuropathy (CIDP)

- **Search query:** What evidence supports this novel treatment for adult patients with chronic inflammatory demyelinating polyneuropathy (CIDP)?

- **Top match:** `RT-101` (tier: P) from `HYQVIA_USA_ENG` (score: 0.03)

**Sub-assertions:**

- ❌ A novel treatment
- ✅ For adult patients with chronic inflammatory demyelinating polyneuropathy (CIDP)
  > *"HIZENTRA is indicated for the treatment of adult patients with chronic inflammatory demyelinating polyneuropathy (CIDP) as maintenance therapy to prev"*

**Assessment:** Claim is only partially substantiated - while evidence supports CIDP treatment indication for adults, the 'novel' characterization is not supported by any provided evidence.

---

### #6 (Row 10) — ✅ PASS (95.0%)

- **CT-ID:** `CT-604` | **Time:** 15.2s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** The liquid medicine should be clear to pale yellow.

- **Search query:** What evidence supports that this liquid medicine should be clear to pale yellow?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.048)

**Sub-assertions:**

- ✅ The liquid medicine should be clear to pale yellow
  > *"The liquid medicine should look clear to yellowish in color"*

**Assessment:** The claim is well-substantiated by Primary-tier USPI evidence describing the expected appearance of liquid medicine during inspection.

---

### #7 (Row 11) — ❌ BLOCK (0.0%)

- **CT-ID:** `CT-605` | **Time:** 15.7s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not share the prefilled syringe.

- **Search query:** What evidence supports the recommendation to not share the prefilled syringe?

- **Top match:** `RT-311` (tier: ?) from `Van den Bergh_Eur J Neurol_2021` (score: 0.017)

**Sub-assertions:**

- ❌ Do not share the prefilled syringe

**Assessment:** The claim about not sharing prefilled syringes is not substantiated by any of the provided evidence passages, which focus on CIDP treatment guidelines rather than syringe handling instructions.

---

### #8 (Row 12) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 20.7s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Store VYVGART HYTRULO in the refrigerator between 36°F to 46°F (2°C to 8°C).

- **Search query:** What evidence supports storing VYVGART HYTRULO refrigerated at 36°F to 46°F (2°C to 8°C)?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.049)

**Sub-assertions:**

- ✅ Store VYVGART HYTRULO in the refrigerator
  > *"Store VYVGART HYTRULO in the refrigerator between 36°F to 46°F (2°C to 8°C)"*
- ✅ Temperature range between 36°F to 46°F
  > *"Store VYVGART HYTRULO in the refrigerator between 36°F to 46°F (2°C to 8°C)"*
- ✅ Temperature range between 2°C to 8°C
  > *"Store VYVGART HYTRULO in the refrigerator between 36°F to 46°F (2°C to 8°C)"*

**Assessment:** Fully substantiated storage instruction with exact temperature ranges from Primary-tier PI evidence.

---

### #9 (Row 13) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 15.7s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Keep VYVGART HYTRULO in its original carton to protect from light.

- **Search query:** Does keeping VYVGART HYTRULO in its original carton protect it from light?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.049)

**Sub-assertions:**

- ✅ Keep VYVGART HYTRULO in its original carton
  > *"Keep the prefilled syringes in the original carton"*
- ✅ to protect from light
  > *"to protect them from light until ready to use"*

**Assessment:** Claim is fully substantiated by Primary-tier USPI evidence with exact semantic match for storage instructions.

---

### #10 (Row 14) — ❌ BLOCK (0.0%)

- **CT-ID:** `CT-606` | **Time:** 14.2s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not freeze VYVGART HYTRULO.

- **Search query:** What evidence supports that VYVGART HYTRULO should not be frozen?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.044)

**Sub-assertions:**

- ❌ Do not freeze VYVGART HYTRULO

**Assessment:** The claim 'Do not freeze VYVGART HYTRULO' is not substantiated by any of the provided evidence passages, which contain various safety information and administration instructions but no freezing-related storage guidance.

---

### #11 (Row 15) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 16.5s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not use VYVGART HYTRULO if it has been at room temperature for longer than 30 days.

- **Search query:** What evidence supports not using VYVGART HYTRULO if stored at room temperature for longer than 30 days?

- **Top match:** `RT-302` (tier: ?) from `Hughes_Cochrane Database Syst Rev_2017` (score: 0.017)

**Sub-assertions:**

- ✅ Do not use VYVGART HYTRULO if it has been at room temperature for longer than 30 days
  > *"Do not use the VYVGART HYTRULO prefilled syringe if it has been at room temperature for longer than 30 days."*

**Assessment:** Fully substantiated by Primary-tier evidence from the Prescribing Information with exact verbatim match for the storage instruction.

---

### #12 (Row 17) — ✅ PASS (100.0%)

- **CT-ID:** `CT-603` | **Time:** 18.3s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** After proper instruction on subcutaneous injection technique, a patient or caregiver may inject VYVGART Hytrulo prefilled syringe.

- **Search query:** What evidence supports that, after proper instruction on subcutaneous injection technique, a patient or caregiver may inject VYVGART Hytrulo prefilled syringe?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.049)

**Sub-assertions:**

- ✅ After proper instruction on subcutaneous injection technique, a patient may inject VYVGART Hytrulo prefilled syringe
  > *"VYVGART HYTRULO prefilled syringe may be administered by patients and/or caregivers after proper instruction in subcutaneous injection technique"*
- ✅ After proper instruction on subcutaneous injection technique, a caregiver may inject VYVGART Hytrulo prefilled syringe
  > *"VYVGART HYTRULO prefilled syringe may be administered by patients and/or caregivers after proper instruction in subcutaneous injection technique"*

**Assessment:** Claim is fully substantiated by Primary-tier PI evidence that explicitly states patients and caregivers may administer the prefilled syringe after proper instruction in subcutaneous injection technique.

---

### #13 (Row 20) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 15.4s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Direct patients to read the full Instructions for Use prior to self-injecting the prefilled syringe.

- **Search query:** What evidence supports directing patients to read the full Instructions for Use before self-injecting a prefilled syringe?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.04)

**Sub-assertions:**

- ✅ Direct patients to read the full Instructions for Use
  > *"Be sure to read and understand this Instructions for Use before injecting VYVGART HYTRULO."*
- ✅ Prior to self-injecting the prefilled syringe
  > *"Be sure to read and understand this Instructions for Use before injecting VYVGART HYTRULO."*

**Assessment:** The claim is fully substantiated by the Instructions for Use, which explicitly instructs patients to read and understand the IFU before injecting VYVGART HYTRULO.

---

### #14 (Row 25) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 14.3s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** The prefilled syringe should always be kept out of reach of children.

- **Search query:** What evidence supports keeping the prefilled syringe out of reach of children?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.042)

**Sub-assertions:**

- ✅ The prefilled syringe should always be kept out of reach of children
  > *"Keep VYVGART HYTRULO and all medicines out of the reach of children."*

**Assessment:** The claim is fully substantiated by Primary-tier evidence from the US Prescribing Information with a close semantic match for this product handling instruction.

---

### #15 (Row 27) — ✅ PASS (100.0%)

- **CT-ID:** `CT-603` | **Time:** 15.0s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** For subcutaneous injection over 20 to 30 seconds

- **Search query:** What evidence supports subcutaneous injection administration over 20 to 30 seconds?

- **Top match:** `RT-101` (tier: P) from `hizentra-prescribing-information` (score: 0.041)

**Sub-assertions:**

- ✅ For subcutaneous injection
  > *"For subcutaneous infusion only."*
- ✅ over 20 to 30 seconds
  > *"It will take about **20 to 30 seconds** to inject all of the liquid medicine."*

**Assessment:** Claim is fully substantiated by Primary-tier USPI sources covering both subcutaneous administration route and specific injection timeframe.

---

### #16 (Row 28) — ✅ PASS (100.0%)

- **CT-ID:** `CT-604` | **Time:** 21.8s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** For single-dose prefilled syringes

- **Search query:** What evidence supports the use of single-dose prefilled syringes?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.048)

**Sub-assertions:**

- ✅ For single-dose prefilled syringes
  > *"Single-Dose Prefilled Syringe"*

**Assessment:** The claim is fully substantiated by Primary-tier evidence from the VYVGART HYTRULO prescribing information which explicitly mentions single-dose prefilled syringes.

---

### #17 (Row 32) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 16.9s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Prefilled syringe may be stored at room temperature at up to 86 °F (30 °C).

- **Search query:** What evidence supports that a prefilled syringe may be stored at room temperature up to 86 °F (30 °C)?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.048)

**Sub-assertions:**

- ✅ Prefilled syringe may be stored at room temperature
  > *"If needed, prefilled syringes may be stored at room temperature at up to 30°C (86°F) in the original carton for a single period of up to 30 days after"*
- ✅ Storage temperature up to 86°F (30°C)
  > *"If needed, prefilled syringes may be stored at room temperature at up to 30°C (86°F) in the original carton for a single period of up to 30 days after"*

**Assessment:** Claim is fully substantiated by Primary-tier PI evidence with exact temperature specifications matching verbatim.

---

### #18 (Row 34) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 15.0s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Patients should keep the prefilled syringe in the original carton to protect it from light until ready to use.

- **Search query:** What evidence supports keeping the prefilled syringe in the original carton to protect it from light until ready to use?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.045)

**Sub-assertions:**

- ✅ Patients should keep the prefilled syringe in the original carton
  > *"Keep the prefilled syringes in the original carton"*
- ✅ to protect it from light
  > *"to protect them from light"*
- ✅ until ready to use
  > *"until ready to use"*

**Assessment:** Claim is fully substantiated by verbatim text from the VYVGART HYTRULO Prescribing Information regarding proper storage of prefilled syringes in original carton to protect from light until ready to use.

---

### #19 (Row 35) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 15.7s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Tell your patients that they can also store the prefilled syringe at room temperature for up to 30 days.

- **Search query:** What evidence supports storing the prefilled syringe at room temperature for up to 30 days?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.045)

**Sub-assertions:**

- ✅ Patients can store the prefilled syringe at room temperature
  > *"Single-dose prefilled syringe may be stored at room temperature (up to 86°F (30°C)) for up to 30 days."*
- ✅ Storage at room temperature is for up to 30 days
  > *"Single-dose prefilled syringe may be stored at room temperature (up to 86°F (30°C)) for up to 30 days."*

**Assessment:** Claim is fully substantiated by VYVGART HYTRULO PI which explicitly states prefilled syringes may be stored at room temperature for up to 30 days.

---

### #20 (Row 37) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 17.5s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Place the remaining prefilled syringes in the carton back into the refrigerator for later use.

- **Search query:** What evidence supports refrigerating remaining prefilled syringes in the carton for later use?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.049)

**Sub-assertions:**

- ✅ Place the remaining prefilled syringes in the carton back into the refrigerator for later use
  > *"Remove 1 prefilled syringe from the carton (see Figure D) and place any remaining prefilled syringes back into the refrigerator for later use."*

**Assessment:** The claim is fully substantiated by verbatim instruction from the VYVGART HYTRULO Prescribing Information regarding proper storage of remaining prefilled syringes.

---

### #21 (Row 39) — ❌ BLOCK (0.0%)

- **CT-ID:** `CT-605` | **Time:** 14.6s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Discard any unused portion

- **Search query:** What evidence supports this claim?

- **Top match:** `RT-302` (tier: ?) from `Hughes_Cochrane Database Syst Rev_2017` (score: 0.017)

**Sub-assertions:**

- ❌ Discard any unused portion

**Assessment:** No substantiation found. The claim requires product handling/disposal instructions but all evidence relates to CIDP research and contains no product-specific disposal guidance.

---

### #22 (Row 40) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 18.6s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** First, patients need to check the expiration date.

- **Search query:** What evidence supports that patients should check the expiration date?

- **Top match:** `RT-901` (tier: ?) from `DOF_EFG-HF-PFS-gMG-2342 and CIDP-2401 Human Factor Stud` (score: 0.018)

**Sub-assertions:**

- ✅ Patients need to check the expiration date
  > *"Check expiration date - Does not identify to check expiration date on the syringe label"*

**Assessment:** The claim is substantiated by the evidence text but uses insufficient source tier. Product administration instructions should come from PI/USPI rather than human factors studies.

---

### #23 (Row 41) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 21.2s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Check the expiration date. Ensure the prefilled syringe isn't cracked, broken, or damaged. Double check prefilled syringe cap isn't missing. Make sure medicine is clear to yellowish in color.

- **Search query:** What evidence supports checking expiration date, syringe integrity, cap presence, and that medicine is clear to yellowish before using a prefilled syringe?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.047)

**Sub-assertions:**

- ✅ Check the expiration date
  > *"Check the expiration date on the prefilled syringe label (see Figure F)."*
- ✅ Ensure the prefilled syringe isn't cracked, broken, or damaged
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*
- ✅ Double check prefilled syringe cap isn't missing
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*
- ✅ Make sure medicine is clear to yellowish in color
  > *"The liquid medicine should look clear to yellowish in color."*

**Assessment:** All sub-assertions are fully substantiated by verbatim or semantically equivalent instructions from the official Instructions for Use documentation.

---

### #24 (Row 42) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 15.6s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Next, they'll make sure the prefilled syringe isn't cracked, broken, or damaged.

- **Search query:** What evidence supports checking that a prefilled syringe is not cracked, broken, or damaged before use?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.044)

**Sub-assertions:**

- ✅ They'll make sure the prefilled syringe isn't cracked
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*
- ✅ They'll make sure the prefilled syringe isn't broken
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*
- ✅ They'll make sure the prefilled syringe isn't damaged
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*

**Assessment:** Claim is fully substantiated by the IFU which explicitly instructs users to check that the prefilled syringe is not cracked, broken, or damaged.

---

### #25 (Row 43) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 12.8s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** After that, they'll need to make sure the prefilled syringe cap isn't missing.

- **Search query:** What evidence supports that users must ensure the prefilled syringe cap is not missing?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.042)

**Sub-assertions:**

- ✅ They'll need to make sure the prefilled syringe cap isn't missing
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*

**Assessment:** The claim is fully substantiated by the IFU which explicitly instructs users not to use the prefilled syringe if the cap is missing.

---

### #26 (Row 44) — ✅ PASS (100.0%)

- **CT-ID:** `CT-604` | **Time:** 15.5s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** And finally, patients should look to see that the medicine is clear to yellowish in color.

- **Search query:** What evidence supports that patients should verify the medicine is clear to yellowish in color?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.042)

**Sub-assertions:**

- ✅ Patients should look to see that the medicine is clear to yellowish in color
  > *"The liquid medicine should look clear to yellowish in color"*

**Assessment:** The claim is fully substantiated by Primary-tier evidence from the VYVGART HYTRULO prescribing information, which provides the exact visual inspection instruction for patients.

---

### #27 (Row 45) — ✅ PASS (100.0%)

- **CT-ID:** `CT-604` | **Time:** 13.5s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** A little cloudiness is normal.

- **Search query:** Is a little cloudiness considered normal for this product?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.049)

**Sub-assertions:**

- ✅ A little cloudiness is normal
  > *"A little cloudiness is normal."*

**Assessment:** Claim is fully substantiated by verbatim text from VYVGART HYTRULO PI regarding normal appearance of liquid medicine in prefilled syringe.

---

### #28 (Row 46) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 12.3s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Check the expiration date

- **Search query:** What is the expiration date of this product?

- **Top match:** `RT-101` (tier: A) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.031)

**Sub-assertions:**

- ✅ Check the expiration date
  > *"Check the expiration date on the prefilled syringe label"*

**Assessment:** The claim is fully substantiated by direct instruction from the VYVGART HYTRULO Prescribing Information to check the expiration date on the prefilled syringe label.

---

### #29 (Row 47) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 16.5s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Ensure the prefilled syringe isn't cracked, broken, or damaged

- **Search query:** What evidence supports inspecting a prefilled syringe to ensure it is not cracked, broken, or damaged?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.044)

**Sub-assertions:**

- ✅ Ensure the prefilled syringe isn't cracked
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*
- ✅ Ensure the prefilled syringe isn't broken
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*
- ✅ Ensure the prefilled syringe isn't damaged
  > *"Do not use the prefilled syringe if it is cracked, broken, damaged, or if the prefilled syringe cap is missing."*

**Assessment:** Claim is fully substantiated by Primary-tier IFU evidence that explicitly instructs users not to use prefilled syringes that are cracked, broken, or damaged.

---

### #30 (Row 48) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 13.7s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Double check prefilled syringe cap isn't missing

- **Search query:** What evidence supports that a prefilled syringe cap should not be missing before use?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.047)

**Sub-assertions:**

- ✅ Check that the prefilled syringe cap is not missing
  > *"Check the condition of the prefilled syringe and the prefilled syringe cap (see Figure G). > Do not use the prefilled syringe if it is cracked, broken"*

**Assessment:** The claim is fully substantiated by the IFU which explicitly instructs users to check the prefilled syringe cap condition and not use if missing.

---

### #31 (Row 49) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 13.9s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Make sure medicine is clear to yellowish in color

- **Search query:** What evidence shows this medicine is clear to yellowish in color?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.04)

**Sub-assertions:**

- ✅ Medicine should be clear to yellowish in color
  > *"The liquid medicine should look clear to yellowish in color"*

**Assessment:** Claim is fully substantiated by verbatim text from Primary-tier Instructions for Use document specifying the exact color requirement for the medicine.

---

### #32 (Row 51) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 15.5s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Warm to room temperature for 30 minutes

- **Search query:** What evidence supports warming to room temperature for 30 minutes?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.049)

**Sub-assertions:**

- ✅ Warm to room temperature
  > *"Allow the prefilled syringe to warm to room temperature"*
- ✅ 30 minutes
  > *"let it sit for at least 30 minutes"*

**Assessment:** Claim is fully substantiated by Primary-tier evidence with exact verbatim match for both warming instruction and 30-minute timeframe.

---

### #33 (Row 52) — ❌ BLOCK (0.0%)

- **CT-ID:** `CT-606` | **Time:** 12.6s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not attempt to warm the prefilled syringe in any other way.

- **Search query:** What evidence supports that prefilled syringes should not be warmed in any other way?

- **Top match:** `RT-101` (tier: P) from `hizentra-prescribing-information` (score: 0.041)

**Sub-assertions:**

- ❌ Do not attempt to warm the prefilled syringe in any other way

**Assessment:** The claim about not warming the prefilled syringe in any other way is completely unsubstantiated by the provided evidence passages, which contain only general handling and administration instructions.

---

### #34 (Row 53) — ❌ BLOCK (0.0%)

- **CT-ID:** `CT-606` | **Time:** 13.6s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not attempt to warm the filled syringe in any other way.

- **Search query:** What evidence supports that a filled syringe should not be warmed in any other way?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.036)

**Sub-assertions:**

- ❌ Do not attempt to warm the filled syringe in any other way

**Assessment:** The claim about not warming the filled syringe in any other way is not substantiated by any of the provided evidence passages, which focus on syringe handling, checking, and administration but do not address warming methods or restrictions.

---

### #35 (Row 54) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 15.4s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** The prefilled syringe should be placed on a flat, clean surface for at least 30 minutes prior to injection.

- **Search query:** What evidence supports placing a prefilled syringe on a flat, clean surface for at least 30 minutes prior to injection?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.037)

**Sub-assertions:**

- ✅ The prefilled syringe should be placed on a flat, clean surface
  > *"Place the prefilled syringe on a clean flat surface"*
- ✅ The prefilled syringe should sit for at least 30 minutes prior to injection
  > *"let it sit for at least 30 minutes"*

**Assessment:** Claim is fully substantiated by Primary-tier evidence from the VYVGART HYTRULO Prescribing Information with exact verbatim matches for both placement and timing requirements.

---

### #36 (Row 55) — ✅ PASS (100.0%)

- **CT-ID:** `CT-606` | **Time:** 15.9s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not use the VYVGART Hytrulo prefilled syringe if it has been at room temperature for longer than 30 days.

- **Search query:** What evidence supports not using VYVGART Hytrulo prefilled syringe after more than 30 days at room temperature?

- **Top match:** `RT-302` (tier: ?) from `Hughes_Cochrane Database Syst Rev_2017` (score: 0.017)

**Sub-assertions:**

- ✅ Do not use the VYVGART Hytrulo prefilled syringe if it has been at room temperature for longer than 30 days
  > *"Do not use the VYVGART HYTRULO prefilled syringe if it has been at room temperature for longer than 30 days."*

**Assessment:** Claim is fully substantiated by verbatim text from the VYVGART HYTRULO Prescribing Information, which is the appropriate primary source for product storage and handling instructions.

---

### #37 (Row 56) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 26.2s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Supplies patients will need: VYVGART Hytrulo pre-filled syringe, Adhesive bandage, Sterile gauze, Alcohol swab, Safety needle (25G, 5/8-inch length, thin wall), FDA-cleared Sharps disposal container

- **Search query:** What supplies are needed for patients using VYVGART Hytrulo pre-filled syringe, including adhesive bandage, sterile gauze, alcohol swab, 25G 5/8-inch safety needle, and FDA-cleared sharps container?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.046)

**Sub-assertions:**

- ✅ VYVGART Hytrulo pre-filled syringe is needed
  > *"You will need supplies that are not provided with VYVGART HYTRULO (see Figure J)."*
- ✅ Adhesive bandage is needed
  > *"* **Sterile Gauze or Small Adhesive Bandage** (As Needed)"*
- ✅ Sterile gauze is needed
  > *"* **Sterile Gauze or Small Adhesive Bandage** (As Needed)"*
- ✅ Alcohol swab is needed
  > *"* **Alcohol Swab** * **Sharps Disposal Container**"*
- ✅ Safety needle (25G, 5/8-inch length, thin wall) is needed
  > *"**Safety Needle (not provided with VYVGART HYTRULO prefilled syringe)** that is 25G, 5/8 inch length, thin wall"*
- ✅ FDA-cleared Sharps disposal container is needed
  > *"**Throw away** the used prefilled syringe, with the needle still attached, **into an FDA-cleared sharps disposal container** right away after use (see"*

**Assessment:** All supply items listed in the claim are fully substantiated by the Instructions for Use documentation with exact specifications provided.

---

### #38 (Row 59) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 23.8s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Once the prefilled syringe has reached room temperature, your patients should then gather the safety needle, alcohol swab, sharps disposal container, and a sterile gauze or a small adhesive bandage.

- **Search query:** What evidence supports that patients should gather a safety needle, alcohol swab, sharps disposal container, and sterile gauze or small adhesive bandage after the prefilled syringe reaches room temperature?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.047)

**Sub-assertions:**

- ✅ Once the prefilled syringe has reached room temperature
  > *"**3 Allow the prefilled syringe to warm to room temperature** **3.1** Place the prefilled syringe on a clean flat surface and **let it sit for at leas"*
- ✅ patients should gather the safety needle
  > *"**Safety Needle (not provided with VYVGART HYTRULO prefilled syringe)** that is 25G, 5/8 inch length, thin wall"*
- ✅ patients should gather alcohol swab
  > *"* **Alcohol Swab** * **Sharps Disposal Container**"*
- ✅ patients should gather sharps disposal container
  > *"* **Alcohol Swab** * **Sharps Disposal Container**"*
- ✅ patients should gather sterile gauze or a small adhesive bandage
  > *"* **Sterile Gauze or Small Adhesive Bandage** (As Needed)"*

**Assessment:** All components of the claim are fully substantiated by the Instructions for Use, which explicitly lists all required supplies and confirms the room temperature requirement.

---

### #39 (Row 60) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 20.5s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Supplies patients will need: Adhesive bandage, Sterile gauze, Alcohol swab, Safety needle (25G, 5/8-inch length, thin wall), FDA-cleared Sharps disposal container

- **Search query:** What patient supplies are needed, including safety needle (25G, 5/8-inch, thin wall) and FDA-cleared sharps disposal container?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.045)

**Sub-assertions:**

- ✅ Adhesive bandage
  > *"Sterile Gauze or Small Adhesive Bandage"*
- ✅ Sterile gauze
  > *"Sterile Gauze or Small Adhesive Bandage"*
- ✅ Alcohol swab
  > *"Alcohol Swab"*
- ✅ Safety needle (25G, 5/8-inch length, thin wall)
  > *"Safety Needle (not provided with VYVGART HYTRULO prefilled syringe) that is 25G, 5/8 inch length, thin wall"*
- ✅ FDA-cleared Sharps disposal container
  > *"into an FDA-cleared sharps disposal container"*

**Assessment:** All supply items are explicitly listed in the Instructions for Use with exact specifications where applicable.

---

### #40 (Row 61) — ⚠️ SOFT_FLAG (75.0%)

- **CT-ID:** `CT-605` | **Time:** 19.8s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Patients should always wash their hands prior to preparing the prefilled syringe for self-injection.

- **Search query:** What evidence supports that patients should always wash hands before preparing a prefilled syringe for self-injection?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.049)

**Sub-assertions:**

- ✅ Patients should wash their hands
  > *"Wash your hands with soap and water"*
- ✅ Hand washing should occur prior to preparing the prefilled syringe
  > *"4 Gather supplies and wash your hands"*
- ✅ This applies to self-injection preparation
  > *"8 Give the injection"*
- ❌ Patients should always wash their hands

**Assessment:** The claim is substantially supported by the IFU which instructs hand washing prior to syringe preparation, but the qualifier 'always' is not present in the evidence.

---

### #41 (Row 62) — ⚠️ SOFT_FLAG (75.0%)

- **CT-ID:** `CT-605` | **Time:** 17.9s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Patients should always wash their hands with soap and water prior to self-injection.

- **Search query:** What evidence supports washing hands with soap and water prior to self-injection?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.049)

**Sub-assertions:**

- ✅ Patients should wash their hands with soap and water
  > *"Wash your hands with soap and water"*
- ✅ Hand washing should occur prior to self-injection
  > *"Wash your hands with soap and water"*
- ✅ This instruction applies to patients performing self-injection
  > *"This Instructions for Use contains information on how to inject VYVGART HYTRULO"*
- ❌ Patients should always perform this hand washing

**Assessment:** The claim is substantially supported by the Instructions for Use, but the absolute qualifier 'always' is not present in the evidence.

---

### #42 (Row 63) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 13.7s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not touch the tip of the prefilled syringe after the prefilled syringe cap has been removed.

- **Search query:** What evidence supports avoiding contact with the tip of a prefilled syringe after the cap has been removed?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.046)

**Sub-assertions:**

- ✅ Do not touch the tip of the prefilled syringe after the prefilled syringe cap has been removed
  > *"Do not touch the tip of the prefilled syringe after the prefilled syringe cap has been removed."*

**Assessment:** Claim is fully substantiated with exact verbatim match from Primary-tier IFU source.

---

### #43 (Row 64) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 14.0s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Patients will carefully open the safety needle package and remove the needle.

- **Search query:** What evidence supports that patients will carefully open the safety needle package and remove the needle?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.048)

**Sub-assertions:**

- ✅ Patients will carefully open the safety needle package
  > *"Carefully open the safety needle package and remove the needle"*
- ✅ Patients will remove the needle
  > *"Carefully open the safety needle package and remove the needle"*

**Assessment:** The claim is fully substantiated by verbatim instructions from the primary-tier Instructions for Use document.

---

### #44 (Row 65) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 14.0s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Instruct patients to throw away the packaging in the household trash.

- **Search query:** What evidence supports instructing patients to throw away the packaging in the household trash?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.048)

**Sub-assertions:**

- ✅ Instruct patients to throw away the packaging in the household trash
  > *"Throw away the packaging into household trash."*

**Assessment:** Claim is fully substantiated by verbatim instruction in the Primary-tier IFU regarding disposal of needle packaging in household trash.

---

### #45 (Row 66) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 16.7s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Bend the prefilled syringe cap to one side to snap it off and remove it from the prefilled syringe.

- **Search query:** What evidence supports bending the prefilled syringe cap to one side to snap it off for safe removal from the prefilled syringe?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.049)

**Sub-assertions:**

- ✅ Bend the prefilled syringe cap to one side
  > *"Bend the prefilled syringe cap to one side to snap it off and remove it from the prefilled syringe"*
- ✅ Snap it off
  > *"Bend the prefilled syringe cap to one side to snap it off and remove it from the prefilled syringe"*
- ✅ Remove it from the prefilled syringe
  > *"Bend the prefilled syringe cap to one side to snap it off and remove it from the prefilled syringe"*

**Assessment:** Complete substantiation. The claim is verbatim identical to the instruction in the IFU, providing exact procedural guidance for cap removal.

---

### #46 (Row 67) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 14.8s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Patients can throw away the prefilled syringe cap in the household trash.

- **Search query:** What evidence supports that patients can discard the prefilled syringe cap in household trash?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.048)

**Sub-assertions:**

- ✅ Patients can throw away the prefilled syringe cap
  > *"Throw away the prefilled syringe cap into the household trash."*
- ✅ The disposal method is household trash
  > *"Throw away the prefilled syringe cap into the household trash."*

**Assessment:** Claim is fully substantiated by Primary-tier IFU with exact verbatim instruction for household trash disposal of prefilled syringe cap.

---

### #47 (Row 68) — ✅ PASS (100.0%)

- **CT-ID:** `CT-605` | **Time:** 18.4s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Holding the prefilled syringe by the syringe body in one hand, patients should attach the safety needle to the prefilled syringe by twisting it to the right or clockwise until they feel resistance.

- **Search query:** What evidence supports attaching a safety needle to a prefilled syringe by twisting right/clockwise until resistance is felt while holding the syringe body?

- **Top match:** `RT-104` (tier: P) from `VYVGART Hytrulo gMG + CIDP Instructions For Use (IFU)` (score: 0.049)

**Sub-assertions:**

- ✅ Holding the prefilled syringe by the syringe body in one hand
  > *"Hold the prefilled syringe by the syringe body in one hand"*
- ✅ Patients should attach the safety needle to the prefilled syringe
  > *"attach the safety needle to the prefilled syringe by twisting it"*
- ✅ By twisting it to the right or clockwise
  > *"by twisting it to the right (clockwise)"*
- ✅ Until they feel resistance
  > *"until you feel resistance"*

**Assessment:** Complete substantiation - all procedural steps for needle attachment are verbatim matched in the IFU with exact instructions.

---

### #48 (Row 73) — ✅ PASS (100.0%)

- **CT-ID:** `CT-603` | **Time:** 18.4s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not inject into skin that is irritated, red, bruised, infected, or tender.

- **Search query:** What evidence supports avoiding injection into skin that is irritated, red, bruised, infected, or tender?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.047)

**Sub-assertions:**

- ✅ Do not inject into skin that is irritated
  > *"Do not inject into skin that is irritated, red, bruised, infected, or tender."*
- ✅ Do not inject into skin that is red
  > *"Do not inject into skin that is irritated, red, bruised, infected, or tender."*
- ✅ Do not inject into skin that is bruised
  > *"Do not inject into skin that is irritated, red, bruised, infected, or tender."*
- ✅ Do not inject into skin that is infected
  > *"Do not inject into skin that is irritated, red, bruised, infected, or tender."*
- ✅ Do not inject into skin that is tender
  > *"Do not inject into skin that is irritated, red, bruised, infected, or tender."*

**Assessment:** Claim is fully substantiated with exact verbatim match from VYVGART HYTRULO Prescribing Information administration instructions.

---

### #49 (Row 74) — ✅ PASS (100.0%)

- **CT-ID:** `CT-603` | **Time:** 14.9s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not inject into skin that is hard, scarred, or has moles.

- **Search query:** What evidence supports avoiding injection into skin that is hard, scarred, or has moles?

- **Top match:** `RT-101` (tier: P) from `vyvgart-hytrulo-prescribing-information_3.26` (score: 0.047)

**Sub-assertions:**

- ✅ Do not inject into skin that is hard, scarred, or has moles
  > *"Do not inject into skin that is hard, scarred, or has moles."*

**Assessment:** Claim is fully substantiated with exact verbatim match from Primary-tier source (USPI). This is an administration instruction claim appropriately supported by the prescribing information.

---

### #50 (Row 75) — ❌ BLOCK (0.0%)

- **CT-ID:** `CT-603` | **Time:** 12.7s
- **Document:** 25-VYVCIDP-1365_CIDP_PFS_video_storyboard_v26
- **Claim:** Do not inject into a vein.

- **Search query:** What evidence supports avoiding intravenous injection for this treatment?

- **Top match:** `RT-101` (tier: P) from `hizentra-prescribing-information` (score: 0.033)

**Sub-assertions:**

- ❌ Do not inject into a vein

**Assessment:** The claim 'Do not inject into a vein' is not substantiated by any of the provided evidence passages, which describe subcutaneous administration but do not explicitly prohibit intravenous injection.

---
