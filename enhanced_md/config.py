import roman


NUMBERING_TYPE_REGEX = {
    "bullet": r"\u2022",  # •, TODO: Find commonly used bullet characters
    "decimal": r"\d+",
    "decimalZero": r"0*\d+",
    "decimalEnclosedCircle": r"",
    "decimalEnclosedFullStop": r"\d+\.",
    "decimalEnclosedParen": r"\(\d+\)",
    "cardinalText": r"",  # TODO: Find for all languages
    "ordinalText": r"",  # TODO: Find for all languages
    "lowerLetter": r"[a-z]+",  # TODO: Find for all alphabets
    "upperLetter": r"[A-Z]",  # TODO: Find for all alphabets
    "lowerRoman": r"s{0,4}(m{0,4})(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})",
    "upperRoman": r"S{0,4}(M{0,4})(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})",
    "chicago": r"",
    "none": r"",
}

def int_to_lowerLetter(x: int) -> str:
    return "" if x == 0 else int_to_lowerLetter((x - 1)//26) + chr((x-1) % 26 + 97)


NUMBERING_TYPE_INT_TO_STR = {
    "bullet": "\u2022",  # •, TODO: Find commonly used bullet characters
    "decimal": lambda x: str(x),
    "decimalZero": "TODO",
    "decimalEnclosedCircle": r"TODO",
    "decimalEnclosedFullStop": lambda x: f"{x}.",
    "decimalEnclosedParen": lambda x: f"({x})",
    "cardinalText": r"",  # TODO: Find for all languages
    "ordinalText": r"",  # TODO: Find for all languages
    "lowerLetter": lambda x: int_to_lowerLetter(x),  # TODO: Find for all alphabets
    "upperLetter": lambda x: int_to_lowerLetter(x).upper(),
    "lowerRoman": lambda x: roman.toRoman(x).lower(),
    "upperRoman": lambda x: roman.toRoman(x),
    "chicago": "TODO",
    "none": lambda x: "",
}


NUMBERING_TYPE_STR_TO_INT = {
    "bullet": 0,  # •, TODO: Define well those that do not have an inherit int value
    "decimal": lambda x: int(x),
    "decimalZero": lambda x: int(x),
    "decimalEnclosedCircle": r"TODO",
    "decimalEnclosedFullStop": lambda x: int(x.rstrip(".")),
    "decimalEnclosedParen": lambda x: int(x.strip("()")),
    "cardinalText": r"",  # TODO: Find for all languages
    "ordinalText": r"",  # TODO: Find for all languages
    "lowerLetter": lambda x: sum((ord(char) - 96) * (26 ** i) for i, char in enumerate(reversed(x))),  # TODO: Find for all alphabets
    "upperLetter": lambda x: sum((ord(char) - 96) * (26 ** i) for i, char in enumerate(reversed(x.lower()))),
    "lowerRoman": lambda x: roman.fromRoman(x.upper()),
    "upperRoman": lambda x: roman.fromRoman(x),
    "chicago": "TODO",
    "none": 0,
}
