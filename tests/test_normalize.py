from arabic_eval.normalize import normalise_text, parse_date, parse_number, to_arabic_indic, to_western_digits


def test_digits_both_ways():
    assert to_western_digits("٢٠٢٦/١١٨") == "2026/118"
    assert to_western_digits("۱۲۳") == "123"  # Persian/Urdu digits too
    assert to_arabic_indic("2026") == "٢٠٢٦"


def test_normalise_folds_letter_forms_marks_and_digits():
    assert normalise_text("شَرِكَةُ السَّلامِ") == normalise_text("شركة السلام")
    assert normalise_text("أبوظبي") == normalise_text("ابوظبى")
    assert normalise_text("ـمـرحـبـا") == normalise_text("مرحبا")  # tatweel
    assert normalise_text("رقم ١٢٣") == normalise_text("رقم 123")


def test_parse_number_arabic_separators():
    assert parse_number("٦٬٣١٥٫٢٥") == 6315.25
    assert parse_number("١,٢٥٠.٥٠ درهم") == 1250.5
    assert parse_number(42) == 42.0
    assert parse_number("لا يوجد") is None
    assert parse_number(True) is None


def test_parse_date_formats():
    assert parse_date("2026-10-15") == "2026-10-15"
    assert parse_date("١٥/١٠/٢٠٢٦") == "2026-10-15"  # day/month/year
    assert parse_date("١٥ أكتوبر ٢٠٢٦") == "2026-10-15"
    assert parse_date("31/02/2026") is None
    assert parse_date("next week") is None
