import pytest

from app.main import parse_args


@pytest.mark.parametrize("flag", ("--windowed", "--fullscreen"))
def test_explicit_display_mode_is_available_during_launch_verification(flag):
    args = parse_args(["--smoke-test", flag])
    assert args.smoke_test
    assert args.fullscreen == (flag == "--fullscreen")
    assert args.windowed == (flag == "--windowed")


def test_conflicting_display_modes_are_rejected():
    with pytest.raises(SystemExit):
        parse_args(["--fullscreen", "--windowed"])
