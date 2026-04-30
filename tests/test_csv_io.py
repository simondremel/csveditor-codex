from csveditor.csv_io import detect_separator, parse_csv_text, write_csv_text


def test_detect_separator_semicolon():
    text = "a;b;c\n1;2;3\n"
    assert detect_separator(text) == ";"


def test_parse_multiline_and_quotes():
    text = 'a,b\n"hello\nworld",2\n"He said ""yo""",3\n'
    rows, sep = parse_csv_text(text)
    assert sep == ","
    assert rows[1][0] == "hello\nworld"
    assert rows[2][0] == 'He said "yo"'


def test_write_quotes_when_needed():
    out = write_csv_text([[" a ", "x,y", "plain"]], ",")
    assert '" a "' in out
    assert '"x,y"' in out
