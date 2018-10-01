from hotpatch import _make_trampoline, hotpatch


def test_make_trampoline():
    def func(*args, **kwargs):
        return (args, kwargs)

    tramp = _make_trampoline(func)
    assert tramp(1,2,a=1,b=2) == ((1, 2), {'a': 1, 'b': 2})

    
def test_hotpatch_more_freevars():
    def f(a, b):
        return a + b

    c = 123
    def g(a, b):
        return a*b + c

    assert f(3, 3) != g(3, 3)
    restore = hotpatch(g, f)
    assert f(3, 3) == g(3, 3)


def test_hotpatch_less_freevars():
    c = 123
    def f(a, b):
        return a + b + c

    def g(a, b):
        return a*b

    assert f(3, 3) != g(3, 3)
    restore = hotpatch(g, f)
    assert f(3, 3) == g(3, 3)


def test_hotpatch_different_defaults():
    def f(x=123):
        return x

    def g(x=456):
        return x

    assert f() == 123
    hotpatch(g, f)
    assert f() == 456
    assert f(789) == 789

