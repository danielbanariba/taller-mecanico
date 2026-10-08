"""The total in words, in Spanish, generated once at issuance and
stored on the document snapshot (AD-9): a small table-driven function
with no runtime dependency, so a later change to it never alters an
already-issued document.
"""

from typing import Final

from taller.invoicing.domain.errors import AmountInWordsOutOfRange

#: Valid up to L 999,999,999,999.99 (AD-9). Issuance itself already
#: rejects a total this large before `amount_in_words` ever runs
#: (``invoice_amount_too_large``, AD-6); this bound is this function's
#: own defense.
MAX_LEMPIRAS: Final = 999_999_999_999

_UNITS: Final[tuple[str, ...]] = (
    "CERO",
    "UNO",
    "DOS",
    "TRES",
    "CUATRO",
    "CINCO",
    "SEIS",
    "SIETE",
    "OCHO",
    "NUEVE",
    "DIEZ",
    "ONCE",
    "DOCE",
    "TRECE",
    "CATORCE",
    "QUINCE",
    "DIECISÉIS",
    "DIECISIETE",
    "DIECIOCHO",
    "DIECINUEVE",
    "VEINTE",
    "VEINTIUNO",
    "VEINTIDÓS",
    "VEINTITRÉS",
    "VEINTICUATRO",
    "VEINTICINCO",
    "VEINTISÉIS",
    "VEINTISIETE",
    "VEINTIOCHO",
    "VEINTINUEVE",
)

#: Apocope: a number always precedes a noun here (MIL, MILLÓN/MILLONES,
#: LEMPIRA/LEMPIRAS), so 1 and 21 drop their final "-O" (AD-9).
_APOCOPE: Final[dict[int, str]] = {1: "UN", 21: "VEINTIÚN"}

_TENS: Final[dict[int, str]] = {
    3: "TREINTA",
    4: "CUARENTA",
    5: "CINCUENTA",
    6: "SESENTA",
    7: "SETENTA",
    8: "OCHENTA",
    9: "NOVENTA",
}

#: ``CIENTO`` is used only when the group isn't exactly 100 (then it is
#: ``CIEN``, handled separately in `_three_digit_words`).
_HUNDREDS: Final[dict[int, str]] = {
    1: "CIENTO",
    2: "DOSCIENTOS",
    3: "TRESCIENTOS",
    4: "CUATROCIENTOS",
    5: "QUINIENTOS",
    6: "SEISCIENTOS",
    7: "SETECIENTOS",
    8: "OCHOCIENTOS",
    9: "NOVECIENTOS",
}


def _unit_word(n: int) -> str:
    """``n`` in 0..29, apocope'd: it always precedes a noun here."""
    return _APOCOPE.get(n, _UNITS[n])


def _three_digit_words(n: int) -> str:
    """``n`` in 0..999. Empty string for 0 -- the caller decides when a
    bare "CERO" belongs (only at the very top, for a zero amount).
    """
    if n == 0:
        return ""
    hundreds, rest = divmod(n, 100)
    parts = []
    if hundreds:
        parts.append("CIEN" if n == 100 else _HUNDREDS[hundreds])
    if rest:
        if rest < 30:
            parts.append(_unit_word(rest))
        else:
            tens, unit = divmod(rest, 10)
            parts.append(f"{_TENS[tens]} Y {_unit_word(unit)}" if unit else _TENS[tens])
    return " ".join(parts)


def _six_digit_words(n: int) -> str:
    """``n`` in 0..999_999, as ``<hundreds of thousands> MIL <units>``.

    Applying this twice at the top level -- once for the millions
    multiplier, once for the remainder below a million -- is what lets
    `amount_in_words` reach AD-9's full `MAX_LEMPIRAS` bound using only
    the 0..999-sized tables above, with no separate "billion" word.
    """
    if n == 0:
        return ""
    thousands, units = divmod(n, 1000)
    parts = []
    if thousands:
        parts.append("UN MIL" if thousands == 1 else f"{_three_digit_words(thousands)} MIL")
    if units:
        parts.append(_three_digit_words(units))
    return " ".join(parts)


def amount_in_words(total_cents: int) -> str:
    """The Spanish total in words for a document total, in integer
    cents (AD-9). For example ``115000`` (L 1,150.00) is "UN MIL
    CIENTO CINCUENTA LEMPIRAS CON 00/100".

    Raises:
        AmountInWordsOutOfRange: ``total_cents`` is negative, or its
            lempira part exceeds `MAX_LEMPIRAS`.
    """
    if total_cents < 0:
        raise AmountInWordsOutOfRange(total_cents)

    lempiras, cents = divmod(total_cents, 100)
    if lempiras > MAX_LEMPIRAS:
        raise AmountInWordsOutOfRange(total_cents)

    millions, remainder = divmod(lempiras, 1_000_000)

    parts = []
    if millions:
        parts.append("UN MILLÓN" if millions == 1 else f"{_six_digit_words(millions)} MILLONES")
    if remainder or millions == 0:
        parts.append(_six_digit_words(remainder) if remainder else "CERO")

    integer_words = " ".join(parts)
    if millions and remainder == 0:
        # An exact multiple of a million takes "DE" before the currency
        # (AD-9): "UN MILLÓN DE LEMPIRAS".
        integer_words += " DE"

    currency = "LEMPIRA" if lempiras == 1 else "LEMPIRAS"
    return f"{integer_words} {currency} CON {cents:02d}/100"
