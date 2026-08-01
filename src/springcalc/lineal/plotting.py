"""Shared matplotlib backend handling for the library's plotting methods."""
from contextlib import contextmanager
import matplotlib

# Tried in this order; whichever has its GUI bindings installed wins.
INTERACTIVE_BACKENDS = ['TkAgg', 'QtAgg', 'Qt5Agg', 'GTK3Agg', 'GTK4Agg']


@contextmanager
def interactive_backend(show: bool):
    """
    Temporarily switch matplotlib to a real interactive backend so plt.show()
    can open a window, then restore whatever backend was active before.

    The library pins matplotlib to the non-interactive "Agg" backend by
    default (needed for headless web/PDF PNG generation), under which
    plt.show() is a silent no-op. This is only used when show is True;
    otherwise it's a no-op and the current backend is left untouched.
    """
    if not show:
        yield
        return

    original_backend = matplotlib.get_backend()
    for backend in INTERACTIVE_BACKENDS:
        try:
            matplotlib.use(backend, force=True)
            break
        except Exception:
            continue
    else:
        raise RuntimeError(
            "show=True needs an interactive matplotlib backend "
            "(Tk/Qt/GTK bindings), none of which are available here."
        )
    try:
        yield
    finally:
        matplotlib.use(original_backend, force=True)
