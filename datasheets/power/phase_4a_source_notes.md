# Phase 4A targeted implementation evidence

Accessed 2026-09-09. Sources were used for the concrete Sheet 1 selections/pin checks only; no broad component re-audit. The validation record identifies exact pages and claims.

| Local document | Official source / identity |
| --- | --- |
| tps2663_datasheet_rev_g.pdf | https://www.ti.com/lit/ds/symlink/tps2663.pdf — SLVSE94G, June 2024; existing Phase 3 evidence |
| tps3760_datasheet_rev_a.pdf | https://www.ti.com/lit/ds/symlink/tps3760.pdf — SBVS420A, September 2023 |
| csd19537q3_datasheet_rev_b.pdf | https://www.ti.com/lit/ds/symlink/csd19537q3.pdf — SLPS549B, November 2022 |
| bss138lt1_onsemi.pdf | https://www.onsemi.com/download/data-sheet/pdf/bss138lt1-d.pdf — BSS138LT1/D Rev.14, April 2024 |
| tnpw_resistors.pdf | https://www.vishay.com/docs/28758/tnpw_e3.pdf — document 28758, 10-Apr-2026 |
| kemet_c0g.pdf | https://content.kemet.com/datasheets/KEM_C1003_C0G_SMD.pdf — C1003 C0G, 20-Feb-2025 |
| rubycon_zlh.pdf | https://www.rubycon.co.jp/wp-content/uploads/catalog-aluminum/ZLH.pdf — ZLH catalog, revision date not identified |
| amass_xt30_catalog.pdf | https://www.china-amass.com/public/upload/20260207/7fa24f5a6f35ec66c7a115c07a34ab06.pdf — XT30 family catalog, relevant page 10; publication date not inferred from URL |
| amass_xt30pw_product.html | https://www.china-amass.com/biao/273.html — XT30PW product page, with retained spec_0/spec_1 drawing images from its 20241112 image links |

Official web-only evidence, inspected successfully through the web reader; direct binary retrieval returned HTTP 403. No local PDF is falsely claimed:

- [Littelfuse 451/453 datasheet](https://www.littelfuse.com/assetdocs/fuse-451-and-453-datasheet?assetguid=533cd5cc-956c-4243-867f-6ab5a62f6ba1), revised 12/01/25, pp.1–4. Selected 0451010.MRL: 10 A, 125 VDC, 400 A interruption at 32 VDC, 5.6 mΩ nominal cold resistance, 26.46 A²s nominal melting integral. Nano2 451 is nonpolar; ordering suffix MRL is the lead-free reel option. Ratings are not a maximum hot resistance guarantee.
- [TDK C3216X7R1H105K160AB official product record](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3216X7R1H105K160AB) and [characteristic sheet](https://product.tdk.com/en/documents/chara_sheet/C3216X7R1H105K160AB.pdf): 1 uF nominal, ±10%, X7R, 50 VDC, 1206 body 3.2 × 1.6 × 1.6 mm. This record does not turn typical DC-bias curves into a guaranteed effective-capacitance limit.

The AMASS page's `1.5 MΩ` contact-resistance text is retained verbatim as an unresolved source defect; no correction to mΩ is silently made. Its 600 V withstand differs from the catalog's 500 V withstand. Neither discrepancy changes the schematic's logical 1=positive/2=return assignment, but physical mate, contact resistance and footprint qualification remain prerequisites for PCB release.
