hotpatch - In-Place Hotpatching of Python Functions
========

Tested on: Python 3.6.6
Status: experimental

Hotpatching in Python is usually accomplished by replacing
a reference to an existing object with a reference to a
new, patched object. This is how mocking is accomplished
in the `unittest.mock` module from Python's
standard library. However, this approach only takes you
so far, as it relies on being able to replace all the
relevant references to the target object and this is not
always possible.

This method usually works pretty well with methods, as
methods are usually accessed via a reference to a central
class object on which a reference to the target method is
stored, which allows us to replace the reference in a single,
easily-referenced location. However, bound methods can be
copied (e.g. a bound method might be used as a callback),
and these copies will not be affected by the patching of
class object.

Top-level functions are another difficult case. When
a function is accessed via a reference to a module, patching
works pretty well:

```
import hello_world

hello_world.get_message = lambda: "Goodbye, cruel world!"
print(hello_world.get_message()) # prints: Goodbye, cruel world!
```

However, when a function is accessed through a direct
reference, patching is harder:

```
import hello_world
from hello_world import get_message

hello_world.get_message = lambda: "Goodbye, cruel world!"
print(get_message()) # prints: Hello, world!
```

One way around this would be to use `sys.modules` to search
for top-level references to the function in question. However,
this will have a running time proportional to the number of
top-level symbols your program has in all its loaded modules.

A faster, CPython-specific approach (implemented by this
package) is to patch the function object itself by creating
and setting a new `code` object (accessed via the `__code__`
attribute). In the simplest case, this is as easy as the
following:

```
target.__code__ = replacement.__code__
```

However, this is complicated by the fact that not all
code objects are compatible with all function objects.
A function object stores the attribute `__closure__`
containing bindings for the free variables in the
code object. Presumably this is because function
instances produced by the same nested function block
will all the same code but potentially have different
environments. Defaults also need to be stored on the
function object because of cases where the default
is dynamic, e.g.:

```
def outer():
    var = 123
    def inner(x=var):
        return x
    return inner
```

One way in which a code object can be incompatible
with a function object is by having a free variable
count that doesn't match the function's closure
size. To make dealing with these compatibility
issues easier, this package generates a trampoline
code object whose only job is to call the function
with which we are trying to replace the target.
That way, the target function can have whatever
defaults to free variables without interfering
with the patching process.

The trampoline function is generated using the
`bytecode` module from pypi, and the target
function is injected as a constant. The trampoline
code itself doesn't use any free variables, so
our code object starts off with zero free variables.
It can then be made compatible with the target
function closure by adding dummy free variables
to the code object that aren't used by the
bytecode itself.

To keep the trampoline simple, it is defined
as a varargs function that looks something
like this:

```
def trampoline(*args, **kwargs)
    return replacement(*args, **kwargs)
```

You might suspect that if the defaults for the
target are defined on its function object and we
replace the code object with the code object
from the above function, then we would get the
defaults from the original target function.
However, CPython ignores the defaults as the
target's argument count comes from the code
object, and for the above varargs function it
is zero. This is a quirk of the CPython
implementation, which happens not to check if
the function object contains superfluous defaults
that cannot be used by the attached code object.

TODO continue explanation
