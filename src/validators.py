def luhn_check(card_number: str) -> bool:
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13:
        return False

    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d

    return checksum % 10 == 0


def validate_snils(snils: str) -> bool:
    digits = snils.replace("-", "").replace(" ", "")
    return len(digits) == 11 and digits.isdigit()