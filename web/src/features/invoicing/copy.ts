/**
 * All Spanish user-facing strings for the invoicing feature (the fiscal
 * settings screen, the profile and CAI range forms, and later the
 * issuance/credit-note flows) live here, mirroring every other feature's
 * own `copy.ts` convention (`CLAUDE.md`: the API itself never returns
 * Spanish text, except the stored `total_in_words`).
 */
export const invoicingCopy = {
  menuEntry: "Facturación",
  settings: {
    title: "Facturación",
    sarNotice: {
      registration:
        "Antes de emitir documentos reales, registre este sistema ante la SAR y presente la Declaración Jurada correspondiente.",
      accountant: "Confirme este módulo con su contador antes de emitir facturas reales.",
      thermalPaper:
        "Si va a imprimir en papel térmico de 58 mm, use papel certificado para conservar la legibilidad al menos 5 años.",
    },
    readinessTitle: "Estado de facturación",
    documentTypeLabels: {
      "01": "Factura",
      "06": "Nota de crédito",
    } as Record<string, string>,
    readyLabel: (nextNumber: string) => `Listo para emitir. Próximo número: ${nextNumber}.`,
    profileTitle: "Datos fiscales",
    noProfile: "Todavía no ha configurado sus datos fiscales.",
    configureAction: "Configurar",
    editProfileAction: "Editar datos fiscales",
    rangesTitle: "Rangos de CAI",
    noRanges: "Todavía no ha registrado un rango de CAI.",
    registerRangeAction: "Registrar rango",
    remainingLabel: (remaining: number) => `${remaining} números disponibles`,
    deadlineLabel: (isoDate: string) => `Fecha límite: ${isoDate}`,
    backToSettings: "Volver a facturación",
    profileForm: {
      title: "Datos fiscales",
      legalNameLabel: "Razón social",
      legalNameRequired: "La razón social es obligatoria.",
      tradeNameLabel: "Nombre comercial",
      tradeNameRequired: "El nombre comercial es obligatorio.",
      rtnLabel: "RTN",
      rtnRequired: "El RTN es obligatorio.",
      rtnHelper: "14 dígitos, con o sin guiones.",
      addressLabel: "Dirección",
      addressRequired: "La dirección es obligatoria.",
      phoneLabel: "Teléfono",
      phoneRequired: "El teléfono es obligatorio.",
      emailLabel: "Correo electrónico",
      emailRequired: "El correo electrónico es obligatorio.",
      establishmentCodeLabel: "Código de establecimiento",
      establishmentCodeHelper: "3 dígitos, asignados por la SAR.",
      establishmentCodeRequired: "El código de establecimiento es obligatorio.",
      emissionPointCodeLabel: "Código de punto de emisión",
      emissionPointCodeHelper: "3 dígitos, asignados por la SAR.",
      emissionPointCodeRequired: "El código de punto de emisión es obligatorio.",
      submit: "Guardar datos fiscales",
      submitPending: "Guardando...",
    },
    rangeForm: {
      createTitle: "Registrar rango de CAI",
      editTitle: "Editar rango de CAI",
      documentTypeLabel: "Tipo de documento",
      caiLabel: "CAI",
      caiRequired: "El CAI es obligatorio.",
      rangeStartLabel: "Número inicial",
      rangeStartRequired: "El número inicial es obligatorio.",
      rangeEndLabel: "Número final",
      rangeEndRequired: "El número final es obligatorio.",
      issueDeadlineLabel: "Fecha límite de emisión",
      issueDeadlineRequired: "La fecha límite es obligatoria.",
      submit: "Guardar rango",
      submitPending: "Guardando...",
      inUseNotice: "Este rango ya tiene documentos emitidos y no se puede modificar.",
    },
  },
  rangeStateLabels: {
    active: "Activo",
    standby: "En espera",
    exhausted: "Agotado",
    expired: "Vencido",
  } as Record<string, string>,
  offline: {
    profileWriteDisabled: "Conéctese a internet para guardar los datos fiscales.",
    rangeWriteDisabled: "Conéctese a internet para registrar o editar un rango de CAI.",
    issueInvoiceDisabled: "Conéctese a internet para emitir una factura.",
  },
  issue: {
    issueAction: "Emitir factura",
    viewAction: (number: string) => `Ver factura ${number}`,
    dialogTitle: "Emitir factura",
    totalLabel: "Total a facturar",
    nameLabel: "Nombre o razón social",
    nameRequired: "El nombre es obligatorio.",
    rtnLabel: "RTN",
    rtnRequired: "El RTN es obligatorio.",
    identificationRequiredNotice: "Las facturas desde L 10,000.00 requieren el nombre y el RTN del comprador.",
    submit: "Emitir factura",
    submitPending: "Emitiendo...",
  },
  documents: {
    detailTitle: (number: string) => `Factura ${number}`,
    numberLabel: "Número",
    issuedAtLabel: "Fecha de emisión",
    buyerLabel: "Cliente",
    totalLabel: "Total",
    print58mm: "Imprimir 58 mm",
    printLetter: "Imprimir carta",
    backToOrder: "Volver a la orden",
  },
  print: {
    documentName: "FACTURA",
    originalLabel: "ORIGINAL: CLIENTE",
    issuerCopyLabel: "COPIA: EMISOR",
    finalConsumer: "CONSUMIDOR FINAL",
    numberLabel: "Número",
    rangeLabel: "Rango autorizado",
    deadlineLabel: "Fecha límite de emisión",
    dateLabel: "Fecha de emisión",
    issuedAtLabel: "Fecha y hora de emisión",
    buyerLabel: "Cliente",
    descriptionLabel: "Descripción",
    quantityLabel: "Cantidad",
    unitPriceLabel: "Precio unitario",
    exemptLabel: "Exento",
    exoneratedLabel: "Exonerado",
    discountLabel: "Descuento",
    taxableLabel: "Gravado 15%",
    isvLabel: "ISV 15%",
    totalLabel: "Total",
    orderReferenceLabel: "Orden",
    demoWatermark: "DEMOSTRACIÓN — SIN VALOR FISCAL",
    cutHereLabel: "- - - - - cortar aquí - - - - -",
    onlyOriginalToggle: "Solo original",
    printAction: "Imprimir",
  },
};

/**
 * Maps a document-type code to its Spanish label, falling back to the raw
 * code if a future document type arrives before its label does.
 */
export function documentTypeLabel(documentType: string): string {
  return invoicingCopy.settings.documentTypeLabels[documentType] ?? documentType;
}

/** Maps a CAI range's derived state (AD-4) to its Spanish label. */
export function rangeStateLabel(state: string): string {
  return invoicingCopy.rangeStateLabels[state] ?? state;
}

/**
 * Maps `GET /invoicing/settings`'s `blocked_reason` (AD-3/AD-6) to a
 * Spanish explanation of what the workshop still needs to do.
 */
const BLOCKED_REASON_MESSAGES: Record<string, string> = {
  fiscal_profile_missing: "Configure sus datos fiscales para poder emitir.",
  cai_range_missing: "Registre un rango de CAI para poder emitir.",
  cai_range_expired: "El rango de CAI venció. Registre uno nuevo.",
  cai_range_exhausted: "El rango de CAI se agotó. Registre uno nuevo.",
};

const GENERIC_BLOCKED_REASON_MESSAGE = "Todavía no se puede emitir este documento.";

export function getBlockedReasonMessage(reason: string): string {
  return BLOCKED_REASON_MESSAGES[reason] ?? GENERIC_BLOCKED_REASON_MESSAGE;
}

/**
 * Error-code (the `detail` string) to Spanish message mapping, shared by
 * the fiscal profile and CAI range writes. Unknown codes fall back to a
 * generic message, mirroring every other feature's `copy.ts`.
 */
const ERROR_MESSAGES: Record<string, string> = {
  invalid_rtn: "El RTN no es válido. Debe tener 14 dígitos.",
  invalid_phone: "El teléfono no es válido. Use un número hondureño de 8 dígitos.",
  invalid_email: "El correo electrónico no es válido.",
  invalid_establishment_code: "El código de establecimiento debe tener exactamente 3 dígitos.",
  invalid_emission_point_code: "El código de punto de emisión debe tener exactamente 3 dígitos.",
  fiscal_profile_codes_locked:
    "No se pueden cambiar los códigos de establecimiento o punto de emisión mientras tenga un rango de CAI vigente.",
  fiscal_profile_missing: "Configure primero sus datos fiscales.",
  unsupported_document_type: "Ese tipo de documento todavía no está disponible.",
  invalid_cai: "El CAI no es válido.",
  invalid_cai_range: "El rango de números no es válido.",
  cai_deadline_passed: "La fecha límite ya pasó.",
  cai_deadline_too_far: "La fecha límite no puede ser mayor a un año.",
  cai_range_id_conflict: "No se pudo guardar el rango. Intente de nuevo.",
  cai_range_overlap: "Ese rango se traslapa con uno que ya existe.",
  cai_range_not_found: "No se encontró el rango.",
  cai_range_immutable: "Ese rango ya tiene documentos emitidos y no se puede modificar.",
  cai_range_missing: "Registre un rango de CAI para poder emitir.",
  cai_range_expired: "El rango de CAI venció. Registre uno nuevo.",
  cai_range_exhausted: "El rango de CAI se agotó. Registre uno nuevo.",
  buyer_name_required: "Debe indicar el nombre si ingresa el RTN del comprador.",
  buyer_identification_required: "Las facturas desde L 10,000.00 requieren el nombre y el RTN del comprador.",
  work_order_not_invoiceable: "Solo se puede facturar una orden terminada o entregada.",
  work_order_already_invoiced: "Esta orden ya tiene una factura vigente.",
  fiscal_invoice_id_conflict: "No se pudo emitir la factura. Intente de nuevo.",
  invoicing_not_configured: "Configure sus datos fiscales y un rango de CAI para poder facturar.",
  invoice_amount_zero: "No se puede facturar una orden con un total de cero.",
  invoice_amount_too_large: "El monto de la orden es demasiado alto para facturar.",
  fiscal_invoice_not_found: "No se encontró la factura.",
  work_order_not_found: "No se encontró la orden.",
  not_authenticated: "Debe iniciar sesión para continuar.",
  network_error: "No se pudo conectar. Verifique su conexión e intente de nuevo.",
};

const GENERIC_ERROR_MESSAGE = "Ocurrió un error. Intente de nuevo.";

export function getInvoicingErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? GENERIC_ERROR_MESSAGE;
}
