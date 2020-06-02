from pathlib import Path

import pytest

from qncmbe.data_import.origin_import import OriginInterface


@pytest.mark.parametrize(
    "test_in,expected",
    [
        ('"ab"; "', r'%(quote)ab%(quote); %(quote)'),
        ('a\nb', r'a%(lf)b')
    ]
)
def test_sanitize_string(test_in, expected):
    assert OriginInterface.sanitize_string(test_in) == expected


def test_sanitize_path():
    rv = OriginInterface.sanitize_path("asdf/qwerty\\j (k) l.txt")
    assert isinstance(rv, str)


@pytest.mark.parametrize(
    'test_in,passes',
    [
        ('Ab3D4', True),
        ('a b,', False),
        ('', False)
    ]
)
def test_validate_shortname(test_in, passes):
    if passes:
        OriginInterface.validate_shortname(test_in)
    else:
        with pytest.raises(ValueError):
            OriginInterface.validate_shortname(test_in)


def test_OriginInterface():

    thisdir = Path(__file__).resolve().parent
    with OriginInterface() as origin:

        assert origin.load(thisdir/"test in.opj")

        assert origin.activate_workbook('TestBook')
        assert origin.activate_worksheet('TestSheet')

        out_path = thisdir / "test out.opj"
        if out_path.exists():
            out_path.unlink()

        assert origin.save(out_path)

        assert out_path.exists()

        assert origin.activate_workbook('TestBook')
        assert origin.activate_worksheet('TestSheet')
