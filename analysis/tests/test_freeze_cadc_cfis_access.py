from scripts.freeze_cadc_cfis_access import DENIAL, classify_response


def test_authenticated_hidden_table_response_is_access_denied_not_unmatched():
    assert classify_response((DENIAL + "\n").encode()) == "access_denied"


def test_unexpected_response_fails_closed():
    assert classify_response(b"ID\tRA\tDEC\n") == "query_response_unclassified"
