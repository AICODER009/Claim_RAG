# Claim-to-Reference Mapping

This document maps pharmaceutical claim types (CT-IDs) to their acceptable reference types (RT-IDs), grouped by claim group (A1–A11). Each row indicates the appropriate evidence source for substantiating a given claim, along with its tier classification and a regulatory/contextual note.

**Columns:**

- **CT-ID** — Claim Type identifier
- **RT-ID** — Reference Type identifier
- **Reference Category** — Reference category code (B1–B9)
- **Reference Type** — Description of the reference source
- **Tier** — Acceptability tier (P, A, C, N)
- **Note** — Regulatory or methodological note

---

## A1

### CT-101 — Indication claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Verbatim/near-verbatim anchor to approved label. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Verbatim/near-verbatim anchor to approved label. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | Verbatim/near-verbatim anchor to approved label. |
| RT-108 | B1 | Country product label (other) | P | Verbatim/near-verbatim anchor to approved label. |
| RT-102 | B1 | Highlights of Prescribing Information (HPI) | A | Patient-facing label components (US: HPI, MedGuide, PPI; EU: PIL). |
| RT-103 | B1 | Medication Guide (MedGuide) | A | Patient-facing label components (US: HPI, MedGuide, PPI; EU: PIL). |
| RT-106 | B1 | Patient Information Leaflet (PIL) | A | Patient-facing label components (US: HPI, MedGuide, PPI; EU: PIL). |
| RT-112 | B1 | Patient Package Insert (PPI) | A | Patient-facing label components (US: HPI, MedGuide, PPI; EU: PIL). |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Pivotal trial data supporting indication. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Pivotal trial data supporting indication. |
| RT-211 | B2 | Integrated Summary of Efficacy (ISE) | A | Pivotal trial data supporting indication. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Pivotal-trial publication. |
| RT-701 | B7 | FDA approval letter | A | Regulatory approval confirms indication. |
| RT-704 | B7 | EMA EPAR | A | Regulatory approval confirms indication. |
| RT-705 | B7 | Health Canada RDS / SBD | A | Regulatory approval confirms indication. |
| RT-706 | B7 | Other-country public assessment report | A | Regulatory approval confirms indication. |
| RT-707 | B7 | Orange Book / Purple Book listing | A | Orange/Purple Book indication listing. |
| RT-109 | B1 | Company Core Data Sheet (CCDS) | C | Internal master label — use only when product not yet locally approved. |
| RT-110 | B1 | Core Safety Information (CSI / CCSI) | C | Internal master label — use only when product not yet locally approved. |
| RT-310 | B3 | Preprint (bioRxiv / medRxiv / SSRN) | N | Preprint cannot substantiate approved indication. |
| RT-501 | B5 | Claims-data analysis | N | RWE cannot expand indication beyond approved label. |
| RT-502 | B5 | EHR-based study | N | RWE cannot expand indication beyond approved label. |
| RT-503 | B5 | Product / disease registry study | N | RWE cannot expand indication beyond approved label. |
| RT-504 | B5 | Observational cohort study | N | RWE cannot expand indication beyond approved label. |

### CT-102 — Limitation-of-use claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Limitation-of-use text is label-only (21 CFR 201.57(c)(2)(i)(F)). |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Limitation-of-use text is label-only (21 CFR 201.57(c)(2)(i)(F)). |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | Limitation-of-use text is label-only (21 CFR 201.57(c)(2)(i)(F)). |
| RT-108 | B1 | Country product label (other) | P | Limitation-of-use text is label-only (21 CFR 201.57(c)(2)(i)(F)). |
| RT-109 | B1 | Company Core Data Sheet (CCDS) | A | Global master label for multi-country consistency. |
| RT-110 | B1 | Core Safety Information (CSI / CCSI) | A | Global master label for multi-country consistency. |

### CT-103 — Population / subpopulation claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled population/subpopulation (USPI §1/§8, SmPC §4.1/§4.2). |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled population/subpopulation (USPI §1/§8, SmPC §4.1/§4.2). |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | Labeled population/subpopulation (USPI §1/§8, SmPC §4.1/§4.2). |
| RT-108 | B1 | Country product label (other) | P | Labeled population/subpopulation (USPI §1/§8, SmPC §4.1/§4.2). |
| RT-216 | B2 | Pediatric Investigation Plan (PIP) / PSP report | P | PIP/PSP for pediatric subpopulation claims. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Pivotal trial population definition. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Pivotal trial population definition. |
| RT-211 | B2 | Integrated Summary of Efficacy (ISE) | A | ISE/ISS subgroup tables. |
| RT-212 | B2 | Integrated Summary of Safety (ISS) | A | ISE/ISS subgroup tables. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Published subpopulation analysis. |

### CT-104 — Regulatory status / approval / history

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-701 | B7 | FDA approval letter | P | FDA approval letter (authoritative regulatory-status source). |
| RT-704 | B7 | EMA EPAR | P | EMA EPAR / Health Canada SBD / country PAR — regional equivalents. |
| RT-705 | B7 | Health Canada RDS / SBD | P | EMA EPAR / Health Canada SBD / country PAR — regional equivalents. |
| RT-706 | B7 | Other-country public assessment report | P | EMA EPAR / Health Canada SBD / country PAR — regional equivalents. |
| RT-707 | B7 | Orange Book / Purple Book listing | P | Orange/Purple Book for approval listing. |
| RT-101 | B1 | USPI / US Prescribing Information | A | Label includes approval date on cover/headings. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | A | Label includes approval date on cover/headings. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | A | Label includes approval date on cover/headings. |
| RT-702 | B7 | FDA Medical / Statistical / Clinical Review | A | FDA review documents for approval context. |
| RT-708 | B7 | FDA expedited-designation letter | A | Expedited-designation letters. |

### CT-105 — Designation claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-708 | B7 | FDA expedited-designation letter | P | FDA designation letter (authoritative source for designation claim). |
| RT-701 | B7 | FDA approval letter | A | Approval letter / FDA review for context. |
| RT-702 | B7 | FDA Medical / Statistical / Clinical Review | A | Approval letter / FDA review for context. |
| RT-704 | B7 | EMA EPAR | A | Regional-equivalent designations (EMA orphan, etc.). |
| RT-705 | B7 | Health Canada RDS / SBD | A | Regional-equivalent designations (EMA orphan, etc.). |

### CT-106 — Boxed warning claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Boxed warning is labeled content; must be verbatim. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Boxed warning is labeled content; must be verbatim. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | Boxed warning is labeled content; must be verbatim. |
| RT-108 | B1 | Country product label (other) | P | Boxed warning is labeled content; must be verbatim. |
| RT-111 | B1 | REMS documentation | A | REMS/RMP docs tied to BW risk. |
| RT-605 | B6 | Risk Management Plan (RMP) / REMS | A | REMS/RMP docs tied to BW risk. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | N | Cannot substitute literature for boxed-warning text. |
| RT-301 | B3 | Peer-reviewed full-text journal article | N | Cannot substitute literature for boxed-warning text. |

### CT-107 — Superlative / positioning claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Label claim (e.g., 'first-in-class') if labeled; otherwise non-label superlatives require external factual support. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Label claim (e.g., 'first-in-class') if labeled; otherwise non-label superlatives require external factual support. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | Label claim (e.g., 'first-in-class') if labeled; otherwise non-label superlatives require external factual support. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Trial data supporting the superlative claim's clinical basis. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Trial data supporting the superlative claim's clinical basis. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Trial data supporting the superlative claim's clinical basis. |
| RT-701 | B7 | FDA approval letter | A | Approval/designation letter for 'first FDA-approved' claims. |
| RT-707 | B7 | Orange Book / Purple Book listing | A | Orange/Purple Book for 'first generic/biosimilar' claims. |
| RT-708 | B7 | FDA expedited-designation letter | A | Approval/designation letter for 'first FDA-approved' claims. |
| RT-904 | B9 | Third-party licensed data | A | Third-party data for 'most prescribed' claims (IQVIA/Symphony). |

### CT-108 — Contraindication claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Contraindications are labeled content (21 CFR 201.57(c)(5)). |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Contraindications are labeled content (21 CFR 201.57(c)(5)). |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | Contraindications are labeled content (21 CFR 201.57(c)(5)). |
| RT-108 | B1 | Country product label (other) | P | Contraindications are labeled content (21 CFR 201.57(c)(5)). |

### CT-109 — Line-of-therapy claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled line-of-therapy positioning (USPI §1). |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled line-of-therapy positioning (USPI §1). |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | Labeled line-of-therapy positioning (USPI §1). |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Pivotal trial with line-of-therapy design. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Pivotal trial with line-of-therapy design. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of trial. |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | NCCN/ESMO/specialty CPG supporting positioning. |

### CT-110 — Combination / add-on therapy claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Combination must be labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Combination must be labeled. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | Combination must be labeled. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Pivotal combination-therapy trial. |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Pivotal combination-therapy trial. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of combination trial. |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | CPG recommending combination use. |

## A2

### CT-201 — Primary-endpoint efficacy

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §14 Clinical Studies — labeled efficacy. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §14 Clinical Studies — labeled efficacy. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | §14 Clinical Studies — labeled efficacy. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Pivotal A&WC Phase 3 trial (FD&C §505(d)). |
| RT-209 | B2 | Clinical Study Report (CSR) | P | ICH E3 CSR for pivotal trial. |
| RT-211 | B2 | Integrated Summary of Efficacy (ISE) | P | Integrated Summary of Efficacy (NDA). |
| RT-202 | B2 | Phase 2 trial | A | Phase 2 if used as supporting efficacy. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Peer-reviewed publication of pivotal trial. |
| RT-303 | B3 | Meta-analysis | A | Meta-analysis of A&WC trials. |
| RT-305 | B3 | Pooled analysis | A | Pooled analysis across pivotal trials. |
| RT-401 | B4 | Published conference abstract | C | Conference materials: interim/supportive only; prefer peer-reviewed. |
| RT-402 | B4 | Conference poster | C | Conference materials: interim/supportive only; prefer peer-reviewed. |
| RT-403 | B4 | Conference oral presentation | C | Conference materials: interim/supportive only; prefer peer-reviewed. |
| RT-306 | B3 | Review article (narrative) | N | Narrative reviews / editorials / letters not acceptable. |
| RT-307 | B3 | Editorial / commentary | N | Narrative reviews / editorials / letters not acceptable. |
| RT-309 | B3 | Letter to the editor | N | Narrative reviews / editorials / letters not acceptable. |
| RT-310 | B3 | Preprint (bioRxiv / medRxiv / SSRN) | N | Preprint not acceptable for primary-endpoint efficacy. |
| RT-501 | B5 | Claims-data analysis | N | RWE cannot substitute for A&WC pivotal efficacy. |
| RT-502 | B5 | EHR-based study | N | RWE cannot substitute for A&WC pivotal efficacy. |
| RT-504 | B5 | Observational cohort study | N | RWE cannot substitute for A&WC pivotal efficacy. |

### CT-202 — Secondary-endpoint efficacy

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §14 if labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §14 if labeled. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Pre-specified key secondary endpoint from pivotal trial. |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Pre-specified key secondary endpoint from pivotal trial. |
| RT-211 | B2 | Integrated Summary of Efficacy (ISE) | P | Pre-specified key secondary endpoint from pivotal trial. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of pivotal trial including secondary endpoint. |
| RT-303 | B3 | Meta-analysis | A | Meta-analysis/pooled. |
| RT-305 | B3 | Pooled analysis | A | Meta-analysis/pooled. |

### CT-203 — Exploratory / post-hoc endpoint

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | C | Post-hoc acceptable only with CFL-compliant disclosure ('not pre- specified'). |
| RT-209 | B2 | Clinical Study Report (CSR) | C | Post-hoc acceptable only with CFL-compliant disclosure ('not pre- specified'). |
| RT-301 | B3 | Peer-reviewed full-text journal article | C | Published post-hoc with CFL-compliant framing. |
| RT-401 | B4 | Published conference abstract | C | Conference post-hoc with disclosure. |
| RT-402 | B4 | Conference poster | C | Conference post-hoc with disclosure. |
| RT-403 | B4 | Conference oral presentation | C | Conference post-hoc with disclosure. |
| RT-101 | B1 | USPI / US Prescribing Information | N | Post-hoc typically not labeled. |

### CT-204 — Subgroup efficacy

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | A | If subgroup result is in label §14. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | A | If subgroup result is in label §14. |
| RT-211 | B2 | Integrated Summary of Efficacy (ISE) | A | ISE subgroup tables. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Published subgroup analysis. |
| RT-303 | B3 | Meta-analysis | A | Meta-analysis with subgroup forest plot. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | C | Pre-specified subgroup with interaction test; otherwise hypothesis- generating. |
| RT-209 | B2 | Clinical Study Report (CSR) | C | Pre-specified subgroup with interaction test; otherwise hypothesis- generating. |

### CT-205 — Onset-of-action

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled §12.2/§14 onset data. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled §12.2/§14 onset data. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Pivotal trial onset measurement. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Pivotal trial onset measurement. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-206 — Durability / duration-of-effect

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled durability data (§14 long-term cohorts). |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled durability data (§14 long-term cohorts). |
| RT-208 | B2 | Extension / open-label extension (OLE) | P | Open-label extension (OLE) studies. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Pivotal trial with long-term follow-up. |
| RT-207 | B2 | Phase 4 study (post-marketing, general) | A | Phase 4 / PMR / PMC durability data. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Pivotal trial with long-term follow-up. |
| RT-214 | B2 | Post-Marketing Requirement (PMR) study | A | Phase 4 / PMR / PMC durability data. |
| RT-215 | B2 | Post-Marketing Commitment (PMC) study | A | Phase 4 / PMR / PMC durability data. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Long-term follow-up publication. |

### CT-207 — Magnitude-of-effect

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Magnitude derived from pivotal trial; ARR/NNT required alongside RRR (OPDP risk-communication standard). |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Magnitude derived from pivotal trial; ARR/NNT required alongside RRR (OPDP risk-communication standard). |
| RT-211 | B2 | Integrated Summary of Efficacy (ISE) | P | ISE pooled magnitude. |
| RT-101 | B1 | USPI / US Prescribing Information | A | Labeled point estimates. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | A | Labeled point estimates. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |
| RT-303 | B3 | Meta-analysis | A | Meta-analysis/pooled magnitude. |
| RT-305 | B3 | Pooled analysis | A | Meta-analysis/pooled magnitude. |

### CT-208 — Response-rate / responder

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled responder rates. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled responder rates. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Pivotal trial responder analysis. |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Pivotal trial responder analysis. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-209 — Time-to-event / survival

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled §14 time-to-event. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled §14 time-to-event. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Pivotal time-to-event (PFS/OS) analysis. |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Pivotal time-to-event (PFS/OS) analysis. |
| RT-208 | B2 | Extension / open-label extension (OLE) | A | OLE for mature OS/PFS. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

## A3

### CT-301 — Adverse-event / AE-profile

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §6 Adverse Reactions — labeled source of AE-profile claims. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §6 Adverse Reactions — labeled source of AE-profile claims. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | §6 Adverse Reactions — labeled source of AE-profile claims. |
| RT-212 | B2 | Integrated Summary of Safety (ISS) | P | Integrated Summary of Safety (ISS). |
| RT-209 | B2 | Clinical Study Report (CSR) | A | CSR safety sections. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of pivotal or pooled safety. |
| RT-601 | B6 | PBRER / PSUR | A | PBRER/PSUR for updated AE frequencies. |
| RT-604 | B6 | FDA Adverse Event Reporting System (FAERS) | C | FAERS: signal generation only, not denominator-based frequency claims. |

### CT-302 — Tolerability

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled tolerability framing. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled tolerability framing. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Trial-level tolerability endpoints. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Trial-level tolerability endpoints. |
| RT-212 | B2 | Integrated Summary of Safety (ISS) | A | Trial-level tolerability endpoints. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-303 — Comparative safety

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Dedicated head-to-head RCT with active comparator (substantial evidence). |
| RT-209 | B2 | Clinical Study Report (CSR) | P | CSR of head-to-head trial. |
| RT-212 | B2 | Integrated Summary of Safety (ISS) | A | ISS with active-comparator arm. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of head-to-head safety. |
| RT-304 | B3 | Network meta-analysis (NMA) | N | Indirect comparison disallowed (PAAB/OPDP). |
| RT-315 | B3 | Indirect Treatment Comparison (ITC) / MAIC / S | TCN | Indirect comparison disallowed (PAAB/OPDP). |
| RT-501 | B5 | Claims-data analysis | N | RWE alone not sufficient for comparative-safety claims. |
| RT-502 | B5 | EHR-based study | N | RWE alone not sufficient for comparative-safety claims. |
| RT-504 | B5 | Observational cohort study | N | RWE alone not sufficient for comparative-safety claims. |

### CT-304 — Serious-AE / BW-contextualizing

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | BW text is labeled; serious-AE contextualization must cite label. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | BW text is labeled; serious-AE contextualization must cite label. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | BW text is labeled; serious-AE contextualization must cite label. |
| RT-111 | B1 | REMS documentation | A | REMS/RMP tied to risk. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Trial data for risk quantification. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Trial data for risk quantification. |
| RT-212 | B2 | Integrated Summary of Safety (ISS) | A | Trial data for risk quantification. |
| RT-605 | B6 | Risk Management Plan (RMP) / REMS | A | REMS/RMP tied to risk. |

### CT-305 — Drug-interaction

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §7 Drug Interactions — labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §7 Drug Interactions — labeled. |
| RT-205 | B2 | Drug-drug interaction study | P | Dedicated DDI study. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | CSR interaction data. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of DDI study. |

### CT-306 — Long-term / post-marketing safety

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-601 | B6 | PBRER / PSUR | P | PBRER/PSUR for post-marketing cumulative safety. |
| RT-207 | B2 | Phase 4 study (post-marketing, general) | A | Phase 4 / PMR / PMC long-term safety. |
| RT-208 | B2 | Extension / open-label extension (OLE) | A | OLE long-term follow-up. |
| RT-214 | B2 | Post-Marketing Requirement (PMR) study | A | Phase 4 / PMR / PMC long-term safety. |
| RT-215 | B2 | Post-Marketing Commitment (PMC) study | A | Phase 4 / PMR / PMC long-term safety. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Long-term safety publication. |
| RT-603 | B6 | Development Safety Update Report (DSUR) | A | DSUR for investigational products. |
| RT-605 | B6 | Risk Management Plan (RMP) / REMS | A | RMP update. |
| RT-604 | B6 | FDA Adverse Event Reporting System (FAERS) | C | FAERS for signal detection only. |

### CT-307 — Monitoring-requirement / warning-mitigation

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §5 Warnings & Precautions — labeled monitoring text. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §5 Warnings & Precautions — labeled monitoring text. |
| RT-111 | B1 | REMS documentation | A | REMS/RMP if applicable. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Trial data supporting no-monitoring claims. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Trial data supporting no-monitoring claims. |
| RT-605 | B6 | Risk Management Plan (RMP) / REMS | A | REMS/RMP if applicable. |

### CT-308 — Abuse potential / scheduling

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled scheduling/abuse-potential section. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled scheduling/abuse-potential section. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | Labeled scheduling/abuse-potential section. |
| RT-203 | B2 | Phase 1 / FIH / PK study | A | Abuse-liability study. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-309 — Null-safety finding

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-206 | B2 | Thorough QT study | P | Thorough QT study for QTc null claims (ICH E14). |
| RT-101 | B1 | USPI / US Prescribing Information | A | If null finding is labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | A | If null finding is labeled. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | C | Pre-specified null-hypothesis test required; otherwise 'absence of evidence ≠ evidence of absence' trap. |
| RT-209 | B2 | Clinical Study Report (CSR) | C | Pre-specified null-hypothesis test required; otherwise 'absence of evidence ≠ evidence of absence' trap. |
| RT-212 | B2 | Integrated Summary of Safety (ISS) | C | ISS null finding with adequate sample size. |
| RT-301 | B3 | Peer-reviewed full-text journal article | C | Published null result with pre-specification documented. |

### CT-310 — Immunogenicity

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §14.4/§6.2 labeled immunogenicity section. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §14.4/§6.2 labeled immunogenicity section. |
| RT-217 | B2 | Immunogenicity assessment report | P | Immunogenicity assessment report. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Pivotal immunogenicity data. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Pivotal immunogenicity data. |
| RT-218 | B2 | Biosimilar comparability / switching study | A | Biosimilar comparability immunogenicity. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-311 — Pregnancy / lactation / reproductive-toxicity

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §8 PLLR section; SmPC §4.6 — labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §8 PLLR section; SmPC §4.6 — labeled. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | §8 PLLR section; SmPC §4.6 — labeled. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Published pregnancy-exposure analysis. |
| RT-503 | B5 | Product / disease registry study | A | Pregnancy registry data. |
| RT-806 | B8 | Nonclinical / preclinical study publication | A | Animal reproductive-toxicity studies. |

## A4

### CT-401 — Superiority

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Head-to-head A&WC RCT (FDA NI-Trial Guidance). |
| RT-209 | B2 | Clinical Study Report (CSR) | P | CSR of head-to-head. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of head-to-head trial. |
| RT-303 | B3 | Meta-analysis | C | Meta-analysis of head-to-head trials; rigor-dependent. |
| RT-304 | B3 | Network meta-analysis (NMA) | C | Indirect comparison — payer only, not for HCP promotion (PAAB disallows). |
| RT-315 | B3 | Indirect Treatment Comparison (ITC) / MAIC / S | TC C | Indirect comparison — payer only, not for HCP promotion (PAAB disallows). |
| RT-310 | B3 | Preprint (bioRxiv / medRxiv / SSRN) | N | Preprint not acceptable. |
| RT-501 | B5 | Claims-data analysis | N | RWE-based superiority for HCP promotion: high OPDP risk. |
| RT-502 | B5 | EHR-based study | N | RWE-based superiority for HCP promotion: high OPDP risk. |
| RT-504 | B5 | Observational cohort study | N | RWE-based superiority for HCP promotion: high OPDP risk. |

### CT-402 — Non-inferiority

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Head-to-head NI trial with pre-specified margin. |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Head-to-head NI trial with pre-specified margin. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of NI trial. |
| RT-304 | B3 | Network meta-analysis (NMA) | C | Indirect NI — payer only. |
| RT-315 | B3 | Indirect Treatment Comparison (ITC) / MAIC / S | TC C | Indirect NI — payer only. |

### CT-403 — Clinical equivalence (margin-based)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Head-to-head equivalence trial with margin. |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Head-to-head equivalence trial with margin. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-404 — Head-to-head

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Dedicated head-to-head RCT (required). |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Dedicated head-to-head RCT (required). |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-405 — Indirect / cross-trial comparison

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-304 | B3 | Network meta-analysis (NMA) | P | NMA — acceptable for payer audience (AMCP/NICE). |
| RT-315 | B3 | Indirect Treatment Comparison (ITC) / MAIC / S | TC P | MAIC/ITC/STC — acceptable for payer (NICE DSU TSD 18). |
| RT-314 | B3 | HTA appraisal report | A | HTA report containing indirect comparison. |
| RT-510 | B5 | AMCP dossier | A | AMCP dossier incorporating ITC. |
| RT-303 | B3 | Meta-analysis | C | Meta-analysis if clinically interpretable. |
| RT-101 | B1 | USPI / US Prescribing Information | N | Cross-trial comparison not in label; HCP promotion disallowed by PAAB. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | N | Cross-trial comparison not in label; HCP promotion disallowed by PAAB. |

### CT-406 — Class-effect / class-positioning

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled §12 class/MOA framing. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled §12 class/MOA framing. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Published class review. |
| RT-306 | B3 | Review article (narrative) | A | Published class review. |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | Specialty-society guideline referencing class. |
| RT-806 | B8 | Nonclinical / preclinical study publication | A | Nonclinical class-effect support. |

### CT-407 — Biosimilar / interchangeability comparison

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-218 | B2 | Biosimilar comparability / switching study | P | Biosimilar comparability/switching study (required evidence). |
| RT-707 | B7 | Orange Book / Purple Book listing | P | Purple Book interchangeability listing. |
| RT-101 | B1 | USPI / US Prescribing Information | A | Labeled biosimilar/interchangeability designation. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | A | Labeled biosimilar/interchangeability designation. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of comparability study. |
| RT-702 | B7 | FDA Medical / Statistical / Clinical Review | A | FDA review for biosimilar. |
| RT-704 | B7 | EMA EPAR | A | EMA EPAR for biosimilar approval. |

### CT-408 — Market-share / prescribing-pattern

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-904 | B9 | Third-party licensed data | P | Third-party licensed data (IQVIA, Symphony, MMIT) for 'most prescribed'/market-share claims. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Published market-analysis study. |
| RT-902 | B9 | Market research report | C | Market research may support if methodology documented. |

### CT-409 — Switch / transition claim

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-218 | B2 | Biosimilar comparability / switching study | P | Dedicated switching/transition study. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Pivotal trial with switch-arm design. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Pivotal trial with switch-arm design. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |
| RT-501 | B5 | Claims-data analysis | C | RWE switch cohort — high scrutiny for comparative claims. |
| RT-502 | B5 | EHR-based study | C | RWE switch cohort — high scrutiny for comparative claims. |
| RT-503 | B5 | Product / disease registry study | C | RWE switch cohort — high scrutiny for comparative claims. |

## A5

### CT-501 — Mechanism of action (MOA)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §12.1 Mechanism of Action — labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §12.1 Mechanism of Action — labeled. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | §12.1 Mechanism of Action — labeled. |
| RT-203 | B2 | Phase 1 / FIH / PK study | A | Early clinical pharmacology. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |
| RT-806 | B8 | Nonclinical / preclinical study publication | A | Nonclinical MOA support. |

### CT-502 — Pharmacodynamic (PD)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §12.2 Pharmacodynamics — labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §12.2 Pharmacodynamics — labeled. |
| RT-203 | B2 | Phase 1 / FIH / PK study | A | Clinical PK/PD study. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-503 — Pharmacokinetic (PK)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §12.3 Pharmacokinetics — labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §12.3 Pharmacokinetics — labeled. |
| RT-203 | B2 | Phase 1 / FIH / PK study | A | Dedicated PK study. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-504 — Bioavailability

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-204 | B2 | Bioequivalence / bioavailability study | P | Bioavailability study. |
| RT-101 | B1 | USPI / US Prescribing Information | A | Labeled BA parameters. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | A | Labeled BA parameters. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-505 — Bioequivalence

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-204 | B2 | Bioequivalence / bioavailability study | P | Bioequivalence study. |
| RT-707 | B7 | Orange Book / Purple Book listing | P | Orange Book AB-rating. |
| RT-101 | B1 | USPI / US Prescribing Information | A | Labeled BE. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | A | Labeled BE. |

### CT-506 — Pharmacogenomic / biomarker

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §12.5 Pharmacogenomics — labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §12.5 Pharmacogenomics — labeled. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Pivotal trial biomarker-defined subgroup (if pre-specified). |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Pivotal trial biomarker-defined subgroup (if pre-specified). |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |
| RT-803 | B8 | Diagnostic criteria | A | Diagnostic criteria defining the biomarker. |
| RT-806 | B8 | Nonclinical / preclinical study publication | A | Nonclinical biomarker support. |

### CT-507 — Companion-diagnostic (CDx)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled CDx designation (§2, §12). |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled CDx designation (§2, §12). |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | CDx validation publication. |
| RT-701 | B7 | FDA approval letter | A | CDx approval letter. |

## A6

### CT-601 — Dosing / regimen

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §2 Dosage & Administration — labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §2 Dosage & Administration — labeled. |
| RT-107 | B1 | Canadian Product Monograph (CPM) | P | §2 Dosage & Administration — labeled. |
| RT-103 | B1 | Medication Guide (MedGuide) | A | Patient-facing labeling. |
| RT-106 | B1 | Patient Information Leaflet (PIL) | A | Patient-facing labeling. |
| RT-112 | B1 | Patient Package Insert (PPI) | A | Patient-facing labeling. |

### CT-602 — Dose-titration / dose-flexibility

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §2.2/§2.3 labeled dose adjustments. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §2.2/§2.3 labeled dose adjustments. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Trial dose-titration arm. |
| RT-202 | B2 | Phase 2 trial | A | Phase 2 dose-finding. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Trial dose-titration arm. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-603 — Route-of-administration

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §3 Dosage Forms / §2 — labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §3 Dosage Forms / §2 — labeled. |
| RT-104 | B1 | Instructions for Use (IFU) | A | IFU for injection route. |

### CT-604 — Formulation / dosage-form

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §3 / SmPC §6.1 — labeled formulation. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §3 / SmPC §6.1 — labeled formulation. |
| RT-804 | B8 | Pharmacopoeia monograph | A | Pharmacopoeia monograph for generic equivalents. |
| RT-903 | B9 | Manufacturing / CMC data | A | CMC documentation. |

### CT-605 — Device / delivery-system

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-104 | B1 | Instructions for Use (IFU) | P | Instructions for Use (IFU) — primary source for device claims. |
| RT-101 | B1 | USPI / US Prescribing Information | A | Labeled device references. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | A | Labeled device references. |
| RT-903 | B9 | Manufacturing / CMC data | A | CMC/device design data. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | C | Human-factors study from trial. |
| RT-209 | B2 | Clinical Study Report (CSR) | C | Human-factors study from trial. |

### CT-606 — Storage / stability / handling

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §16 Storage / SmPC §6.3-§6.6 — labeled. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §16 Storage / SmPC §6.3-§6.6 — labeled. |
| RT-903 | B9 | Manufacturing / CMC data | A | CMC stability data. |

### CT-607 — Convenience / ease-of-use

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-104 | B1 | Instructions for Use (IFU) | A | IFU describing use. |
| RT-511 | B5 | Patient-preference / utility study | C | Preference/utility study — feature claims must not imply clinical benefit (high OPDP/PAAB scrutiny). |
| RT-805 | B8 | Epidemiology database / surveillance | C | Preference/utility study — feature claims must not imply clinical benefit (high OPDP/PAAB scrutiny). |
| RT-902 | B9 | Market research report | C | Market research — factual-only. |

### CT-608 — Manufacturing / quality / process

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-903 | B9 | Manufacturing / CMC data | P | CMC / manufacturing data. |
| RT-101 | B1 | USPI / US Prescribing Information | A | If labeled (rare). |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | A | If labeled (rare). |
| RT-804 | B8 | Pharmacopoeia monograph | A | Pharmacopoeia purity monograph. |
| RT-301 | B3 | Peer-reviewed full-text journal article | C | Published manufacturing studies — high scrutiny per OPDP 2024 botulinum letter. |

## A7

### CT-701 — Disease prevalence / incidence

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-312 | B3 | WHO / global-health guideline | P | WHO / global-health guideline for prevalence. |
| RT-313 | B3 | Government / public-health guideline | P | CDC / NIH data. |
| RT-805 | B8 | Epidemiology database / surveillance | P | NHANES / SEER / GBD surveillance. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Peer-reviewed epidemiology publication. |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | Specialty-society guideline. |
| RT-503 | B5 | Product / disease registry study | A | Disease registry. |

### CT-702 — Disease burden / morbidity-mortality

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-301 | B3 | Peer-reviewed full-text journal article | P | Peer-reviewed burden-of-illness publication. |
| RT-312 | B3 | WHO / global-health guideline | P | WHO / CDC / NIH data. |
| RT-313 | B3 | Government / public-health guideline | P | WHO / CDC / NIH data. |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | Specialty guideline. |
| RT-314 | B3 | HTA appraisal report | A | HTA report disease-burden section. |
| RT-805 | B8 | Epidemiology database / surveillance | A | Surveillance databases. |

### CT-703 — Unmet-need

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-301 | B3 | Peer-reviewed full-text journal article | P | Peer-reviewed unmet-need analysis. |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | Specialty guideline noting unmet need. |
| RT-312 | B3 | WHO / global-health guideline | A | WHO/CDC/NIH. |
| RT-313 | B3 | Government / public-health guideline | A | WHO/CDC/NIH. |
| RT-314 | B3 | HTA appraisal report | A | HTA report. |

### CT-704 — Diagnostic-criteria / screening

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-803 | B8 | Diagnostic criteria | P | Diagnostic criteria (DSM-5 / ICD-11 / ADA). |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | Specialty-society guideline. |
| RT-802 | B8 | Classification / staging systems | A | Classification/staging systems. |

### CT-705 — Natural-history / disease-progression

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-301 | B3 | Peer-reviewed full-text journal article | P | Peer-reviewed natural-history publication. |
| RT-503 | B5 | Product / disease registry study | P | Disease registry natural-history data. |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | Specialty guideline. |
| RT-504 | B5 | Observational cohort study | A | Observational cohort. |

### CT-706 — Risk-factor

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-301 | B3 | Peer-reviewed full-text journal article | P | Peer-reviewed epidemiology identifying risk factors. |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | Guidelines identifying risk factors. |
| RT-312 | B3 | WHO / global-health guideline | A | Guidelines identifying risk factors. |
| RT-313 | B3 | Government / public-health guideline | A | Guidelines identifying risk factors. |
| RT-805 | B8 | Epidemiology database / surveillance | A | Surveillance database. |

## A8

### CT-801 — Patient-reported outcome (PRO)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | §14 labeled PRO endpoint. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | §14 labeled PRO endpoint. |
| RT-801 | B8 | Validated COA instrument manual | P | Validated COA instrument manual (PRO/ClinRO/ObsRO/PerfO). |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Trial PRO endpoint. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Trial PRO endpoint. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-802 — Health-related quality of life (HRQoL)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled HRQoL endpoint (FDA requires specific labeled domain). |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled HRQoL endpoint (FDA requires specific labeled domain). |
| RT-801 | B8 | Validated COA instrument manual | P | Validated HRQoL instrument (SF-36, EORTC QLQ-C30, etc.). |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Trial HRQoL data. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Trial HRQoL data. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-803 — Functional-status / ADL

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled functional endpoint. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled functional endpoint. |
| RT-801 | B8 | Validated COA instrument manual | P | Validated functional-status COA. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Trial data. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Trial data. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-804 — Symptom-relief

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-101 | B1 | USPI / US Prescribing Information | P | Labeled symptom endpoint. |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | P | Labeled symptom endpoint. |
| RT-801 | B8 | Validated COA instrument manual | P | Validated symptom COA. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Trial symptom data. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Trial symptom data. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-805 — Patient-preference / satisfaction

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-511 | B5 | Patient-preference / utility study | P | Patient-preference/utility study (EQ-5D, TTO, DCE). |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of preference study. |
| RT-902 | B9 | Market research report | C | Market research — factual only; PAAB restrictive. |

### CT-806 — Convenience-as-patient-benefit

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-511 | B5 | Patient-preference / utility study | A | Preference/utility study documenting convenience benefit. |
| RT-801 | B8 | Validated COA instrument manual | A | COA with convenience/burden domain. |
| RT-902 | B9 | Market research report | C | Market research — feature-not-benefit framing required. |

### CT-807 — Testimonial / endorsement

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Peer-reviewed narrative of patient case. |
| RT-101 | B1 | USPI / US Prescribing Information | C | Labeled patient-experience section (rare). |
| RT-105 | B1 | SmPC (Summary of Product Characteristics) | C | Labeled patient-experience section (rare). |
| RT-902 | B9 | Market research report | C | Documented testimonial sources — must meet PAAB/ABPI disclosure. |
| RT-307 | B3 | Editorial / commentary | N | Editorial / opinion endorsement not acceptable. |

## A9

### CT-901 — Cost-effectiveness / cost-utility

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-508 | B5 | Cost-effectiveness / cost-utility analysis | P | Peer-reviewed cost-effectiveness / cost-utility analysis. |
| RT-510 | B5 | AMCP dossier | P | AMCP Format 5.0 dossier. |
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | A | Pivotal trial as input to CEA model. |
| RT-209 | B2 | Clinical Study Report (CSR) | A | Pivotal trial as input to CEA model. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of CEA. |
| RT-314 | B3 | HTA appraisal report | A | HTA appraisal report. |

### CT-902 — Budget-impact

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-509 | B5 | Budget-impact model / analysis | P | Budget-impact model (ISPOR BIM Task Force). |
| RT-510 | B5 | AMCP dossier | P | AMCP dossier BIM section. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Published BIM. |
| RT-501 | B5 | Claims-data analysis | A | Claims/EHR utilization inputs. |
| RT-502 | B5 | EHR-based study | A | Claims/EHR utilization inputs. |

### CT-903 — Cost-offset / cost-savings

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-501 | B5 | Claims-data analysis | P | Administrative claims RWE for cost-offset. |
| RT-502 | B5 | EHR-based study | P | EHR-based cost-offset study. |
| RT-508 | B5 | Cost-effectiveness / cost-utility analysis | P | CEA demonstrating cost-offset. |
| RT-504 | B5 | Observational cohort study | A | Cohort cost-utilization study. |
| RT-510 | B5 | AMCP dossier | A | AMCP dossier. |

### CT-904 — Pharmacoeconomic model

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-508 | B5 | Cost-effectiveness / cost-utility analysis | P | Published CEA / Markov model. |
| RT-510 | B5 | AMCP dossier | P | AMCP dossier. |
| RT-314 | B3 | HTA appraisal report | A | HTA appraisal. |

### CT-905 — Resource-utilization

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-501 | B5 | Claims-data analysis | P | Claims-data HRU analysis. |
| RT-502 | B5 | EHR-based study | P | EHR HRU analysis. |
| RT-504 | B5 | Observational cohort study | A | Cohort HRU. |
| RT-510 | B5 | AMCP dossier | A | Dossier HRU section. |

### CT-906 — Productivity / indirect-cost

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-511 | B5 | Patient-preference / utility study | P | Productivity/utility study. |
| RT-504 | B5 | Observational cohort study | A | Cohort productivity data. |
| RT-508 | B5 | Cost-effectiveness / cost-utility analysis | A | CEA incorporating indirect costs. |
| RT-510 | B5 | AMCP dossier | A | Dossier. |

### CT-907 — Outcomes-threshold (VBC-supporting)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Pivotal trial efficacy threshold. |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Pivotal trial efficacy threshold. |
| RT-510 | B5 | AMCP dossier | P | AMCP dossier with outcomes-threshold section. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |
| RT-508 | B5 | Cost-effectiveness / cost-utility analysis | A | CEA incorporating threshold. |

### CT-908 — Adherence / persistence

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-501 | B5 | Claims-data analysis | P | Claims-data adherence/persistence analysis. |
| RT-502 | B5 | EHR-based study | P | EHR-based persistence. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |
| RT-504 | B5 | Observational cohort study | A | Cohort adherence study. |
| RT-510 | B5 | AMCP dossier | A | Dossier adherence section. |

### CT-909 — Formulary / access / coverage

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-904 | B9 | Third-party licensed data | P | MMIT / Fingertip Formulary data. |
| RT-510 | B5 | AMCP dossier | A | AMCP dossier coverage section. |
| RT-902 | B9 | Market research report | C | Market research on coverage — factual. |

## A10

### CT-A01 — Real-world evidence (RWE)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-501 | B5 | Claims-data analysis | P | RWE sources — RWE claims must cite one of these. |
| RT-502 | B5 | EHR-based study | P | RWE sources — RWE claims must cite one of these. |
| RT-503 | B5 | Product / disease registry study | P | RWE sources — RWE claims must cite one of these. |
| RT-504 | B5 | Observational cohort study | P | RWE sources — RWE claims must cite one of these. |
| RT-505 | B5 | Case-control study | P | RWE sources — RWE claims must cite one of these. |
| RT-506 | B5 | Chart-review study | P | RWE sources — RWE claims must cite one of these. |
| RT-507 | B5 | Pragmatic clinical trial | P | RWE sources — RWE claims must cite one of these. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication of RWE study. |

### CT-A02 — Meta-analysis / systematic review

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-302 | B3 | Systematic review | P | Systematic review. |
| RT-303 | B3 | Meta-analysis | P | Meta-analysis. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | SR/MA published in journal. |

### CT-A03 — Network meta-analysis (NMA)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-304 | B3 | Network meta-analysis (NMA) | P | Network meta-analysis. |
| RT-315 | B3 | Indirect Treatment Comparison (ITC) / MAIC / S | TC P | MAIC / ITC / STC. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | NMA publication. |

### CT-A04 — Pooled analysis (integrated)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-211 | B2 | Integrated Summary of Efficacy (ISE) | P | ISE / ISS integrated analyses. |
| RT-212 | B2 | Integrated Summary of Safety (ISS) | P | ISE / ISS integrated analyses. |
| RT-305 | B3 | Pooled analysis | P | Pooled analysis. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-A05 — Registry-based

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-503 | B5 | Product / disease registry study | P | Product/disease registry study. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Registry publication. |

### CT-A06 — Observational (cohort / case-control)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-504 | B5 | Observational cohort study | P | Observational cohort. |
| RT-505 | B5 | Case-control study | P | Case-control. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |
| RT-506 | B5 | Chart-review study | A | Chart review. |

### CT-A07 — Pragmatic-trial

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-507 | B5 | Pragmatic clinical trial | P | Pragmatic clinical trial. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

### CT-A08 — Single-arm / uncontrolled

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-201 | B2 | Pivotal Phase 3 trial (A&WC) | P | Single-arm pivotal trial (accelerated approval). |
| RT-209 | B2 | Clinical Study Report (CSR) | P | Single-arm pivotal trial (accelerated approval). |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Publication. |

## A11

### CT-B01 — SIUU communication

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-301 | B3 | Peer-reviewed full-text journal article | P | Peer-reviewed full-text article (SIUU primary source — FDA Jan 2025). |
| RT-311 | B3 | Specialty-society clinical practice guideline | P | Clinical practice guideline (SIUU-eligible). |
| RT-302 | B3 | Systematic review | A | SR / meta-analysis as SIUU source. |
| RT-303 | B3 | Meta-analysis | A | SR / meta-analysis as SIUU source. |
| RT-401 | B4 | Published conference abstract | C | Conference materials may qualify under SIUU scientific-soundness criteria. |
| RT-402 | B4 | Conference poster | C | Conference materials may qualify under SIUU scientific-soundness criteria. |
| RT-403 | B4 | Conference oral presentation | C | Conference materials may qualify under SIUU scientific-soundness criteria. |
| RT-310 | B3 | Preprint (bioRxiv / medRxiv / SSRN) | N | Preprint not SIUU-eligible. |
| RT-901 | B9 | Data on File (DoF) | N | Data on File not acceptable for SIUU. |

### CT-B02 — Pre-approval information exchange (PIE)

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-510 | B5 | AMCP dossier | P | AMCP dossier (PIE vehicle). |
| RT-210 | B2 | Clinical Study Protocol / SAP | A | Protocol / SAP disclosure for pre-approval. |
| RT-301 | B3 | Peer-reviewed full-text journal article | A | Peer-reviewed evidence supporting PIE deck. |
| RT-508 | B5 | Cost-effectiveness / cost-utility analysis | A | CEA / BIM for PIE. |
| RT-509 | B5 | Budget-impact model / analysis | A | CEA / BIM for PIE. |

### CT-B03 — HCEI off-label-related

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-508 | B5 | Cost-effectiveness / cost-utility analysis | P | CEA / BIM addressing approved-indication-related economics. |
| RT-509 | B5 | Budget-impact model / analysis | P | CEA / BIM addressing approved-indication-related economics. |
| RT-510 | B5 | AMCP dossier | P | AMCP dossier with HCEI off-label content. |
| RT-501 | B5 | Claims-data analysis | A | RWE for HCEI content. |
| RT-502 | B5 | EHR-based study | A | RWE for HCEI content. |
| RT-504 | B5 | Observational cohort study | A | RWE for HCEI content. |

### CT-B04 — Scientific-exchange

| RT-ID | Ref. Cat. | Reference Type | Tier | Note |
|---|---|---|---|---|
| RT-301 | B3 | Peer-reviewed full-text journal article | P | Peer-reviewed article in response to unsolicited HCP request. |
| RT-302 | B3 | Systematic review | A | SR / MA in response. |
| RT-303 | B3 | Meta-analysis | A | SR / MA in response. |
| RT-311 | B3 | Specialty-society clinical practice guideline | A | CPG in response. |
| RT-901 | B9 | Data on File (DoF) | C | Internal Medical Information Letter / Data on File — industry practice, strict response-only posture. |
