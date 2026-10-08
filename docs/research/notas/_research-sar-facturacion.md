# SAR invoicing rules for a workshop web app (October 2026)

Research note backing the opt-in SAR/CAI invoicing module. It summarizes the rules; it is not legal advice. A Honduran contador should confirm the module before a workshop issues real invoices with it.

## Sources

- **Reglamento:** *Reglamento del Régimen de Facturación, Otros Documentos Fiscales y Registro Fiscal de Imprentas*. This is SAR's consolidated text of Acuerdo 481-2017 (La Gaceta 34,413, 10 Aug 2017) as amended by Acuerdos 609-2017, 725-2018 and 817-2018. It was downloaded from [sar.gob.hn](https://www.sar.gob.hn/download/texto-consolidado-reglamento-del-regimen-de-facturacion-otros-documentos-fiscales-y-registro-fiscal-de-imprentas-contenido-en-el-acuerdo-481-2017-segun-acuerdos-609-2017-725-2018-y-817-2018/) and read in full. Article numbers below refer to it.
- **Código Tributario:** Decreto 170-2016, in SAR's updated text up to Decreto 180-2020, from [sar.gob.hn](https://www.sar.gob.hn/download/texto-actualizado-codigo-tributario-decreto-170-2016-hasta-el-decreto-180-2020-preparado-por-el-departamento-de-asesoria-y-procuracion-legal-de-la-dnj/).
- **Facturación page:** [sar.gob.hn/facturacion](https://www.sar.gob.hn/facturacion/).
- **Secondary:** the [vatupdate Honduras e-invoicing booklet](https://www.vatupdate.com/2026/08/11/honduras-e-invoicing-e-reporting-country-booklet/) (11 Aug 2026) and [PwC Worldwide Tax Summaries](https://taxsummaries.pwc.com/honduras/corporate/other-taxes) (reviewed 10 Aug 2026).

When converting SAR's PDFs to text, the footnote superscripts get fused onto the article numbers: "ARTÍCULO 103." is article 10 with footnote 3. The numbers below are already corrected.

## Electronic invoicing is not mandatory today

- What is in force is the CAI pre-authorization regime of the Reglamento.
- Art. 57 only lets SAR notify taxpayers who must move to electronic emission "conforme a la calendarización por categoría de contribuyente". No such calendar was found.
- vatupdate (Aug 2026) reports that no mandatory structured e-invoicing or DFE regime is in force.
- Acuerdo SAR-236-2024 (an Oficina Virtual for filing returns) is unrelated to invoice clearance. Only the secondary source reports it.
- The search of sar.gob.hn's news and resolutions was not exhaustive, so a newer acuerdo cannot be fully ruled out.

## Modality available to a web app

- **Modalities:** there are two, imprenta and autoimpresor (Art. 50). The autoimpresor media are máquina registradora, sistema computarizado and emisión electrónica (Art. 51). Facturación electrónica (CAEE) is a medio of autoimpresor, not a separate modality (Art. 4.22, 4.9).
- **Sistema computarizado requirements (Art. 53):**
  1. Integrated with at least an accounting or inventory system.
  2. Security mechanisms and audit controls.
  3. Persistence and immediate availability of current and historical transactions.
  4. Optional 2D/3D barcode.
  5. Able to generate text files to transmit to SAR.
- **No software certification:** the taxpayer files a Declaración Jurada that its system meets Art. 53 before being authorized as autoimpresor. Art. 47 only requires registering each system, server and punto de emisión.
- **Who requests authorization:** the taxpayer, not a software provider (Art. 61).
- **CAI scope:** a CAI is per punto de emisión and document type (Art. 59), or for a sistema computarizado, per system and document type (Art. 61).
- **Validity:** at most one year. After the fecha límite de emisión, documents are invalid whatever range remains (Art. 62). A new range may be requested once the current one is exhausted, or within the 2 months before its fecha límite (Art. 59).
- **Tickets:** a Ticket is its own document type and may only come from a registered máquina registradora (Art. 4.27, 4.43, 52). A web app must issue Facturas.
- **Amounts under L 50:** the small-amount exception to issuing a document does not apply to autoimpresor issuers. They must always issue (Art. 9).

## Factura content (Art. 10–11)

- **Printed on every factura:**
  - the issuer's RTN, name or razón social, nombre comercial, address, phone and email;
  - the word "Factura";
  - the CAI, rango autorizado and fecha límite de emisión;
  - the destination of each copy: original to the customer, copy to the issuer.
- **Number:** 16 digits, `NNN-NNN-NN-NNNNNNNN` (establecimiento, punto de emisión, document type `01`, correlative). The correlative restarts at `00000001` after `99999999`.
- **At issuance, buyer with crédito fiscal:**
  - buyer name and RTN, and the date;
  - description, quantity and unit value of each line;
  - amounts broken down as exento, exonerado and gravado by tarifa, with the tax for each tarifa;
  - currency (L), the total in numbers and in words, and discounts.
- **At issuance, consumidor final:** the buyer's name or the legend "CONSUMIDOR FINAL", with the same breakdown, the total and the date. From L 10,000 the buyer must be identified.
- **Exonerated buyers:** the factura carries the exoneration document data.
- **Tax rates:** the Reglamento only asks for a breakdown "por tarifa o alícuota"; the rates come from the Ley del ISV. Per PwC, the general rate is 15%. The 18% rate covers only alcohol, tobacco and premium airline tickets, and no listed exemption covers auto repair labor or parts. That last point is an inference from the PwC list, not checked against the Ley del ISV.
- **No such legend:** "DOCUMENTO NO FISCAL" does not exist in the Reglamento. It is this app's own legend for its non-fiscal receipt.

## Voiding, credit and debit notes

- **ANULADA:** an error caught before delivery is marked "ANULADA", and both copies are kept (Art. 41).
- **After issuance:** reversals, returns and later discounts need a Nota de Crédito, document type `06` (Art. 4.32, 25–26). It references the original's CAI, correlative and date, and carries:
  - the buyer name and RTN;
  - the reason;
  - the total in numbers and in words;
  - the signature and ID of whoever receives it.
- **Debit notes:** a Nota de Débito is type `07` (Art. 27–28).
- **Notifying SAR:** unused or invalid documents must be reported within the first 10 business days of the next month (Art. 42). The 12 listed events include expiry, data change, cessation, theft or loss, and technical failure.

## Printing and delivery

- **Paper:** no minimum paper size or width. Thermal paper is allowed if legibility for at least 5 years is certified (Art. 38).
- **Delivery to an absent customer:** "los medios de envío más convenientes y adecuados" (Art. 14.5). No channel or format is mandated, so a PDF by WhatsApp or email is not explicitly ruled in or out.

## Record keeping

- **Custody:** copies, including voided ones, are kept for the Código Tributario's prescription period and must be available to SAR on request (Art. 5, 41, 43).
- **Libro de ventas:** this Reglamento sets no ledger requirement. The ISV return is monthly, due within the first 10 calendar days of the next month ([sar.gob.hn ISV FAQ](https://www.sar.gob.hn/impuesto-sobre-ventas-isv/)).

## Penalties (Código Tributario)

- **The infraction:** not issuing a fiscal document, or issuing one without the legal requirements, is a falta formal (Art. 149–150, 159).
- **Temporary closure:** that falta is sanctioned with the temporary closure of the establishment (Art. 161).
- **Fine:** it scales with annual gross income (Art. 160 table), from 10% of a minimum wage for income up to L 250,000.
- **Repeat infractions:** a first repeat adds 50%, and a second repeat means indefinite closure until the taxpayer regularizes.

## Implications for the app

- **Modality:** the module makes the app an autoimpresor "sistema computarizado". The workshop registers it, files the Declaración Jurada, requests a CAI per punto de emisión and document type, and types the CAI, range and fecha límite into the app.
- **Range enforcement:** the app must stop issuing when the range runs out or the fecha límite passes, and warn ahead of both.
- **Documents:** Factura `01` first. A Nota de Crédito `06` is the only legal way to correct a delivered invoice. "ANULADA" applies only to an invoice not yet delivered.
- **Settings:** the workshop needs fiscal data (RTN, razón social, address, establecimiento, punto de emisión) and a settings screen. Neither exists today.
- **Buyer:** the customer needs an optional RTN. From L 10,000 a consumidor final must be identified.
- **Content:** totals in words, the tax breakdown by tarifa, and both copies' destinations.
- **Audit:** an issued invoice is immutable. The audit trail and SAR text-file generation (Art. 53) are requirements, not extras.

## Still open

- The prescription period, in years, for document custody (Código Tributario Art. 144–148).
- The ISV rate rules, from the Ley del ISV itself.
- The format of the Art. 53 text files for SAR.
- Art. 17's Ticket code contradiction (09 vs 03), which does not affect facturas.
- Whether issuing without a valid CAI could be a falta material or a delito tributario (Art. 165 onward).
