"""Shared time-expression resolver for edit.json values (see build_edit.py docstring)."""
import json, re
def resolver(marks, timing, extra):
    L = {r['line']: r for r in timing}
    def T(e):
        if isinstance(e, (int, float)): return float(e)
        m = re.fullmatch(r'\s*([A-Za-z_][\w:]*)?\s*([+-]\s*\d*\.?\d+)?\s*', str(e))
        if not m: raise SystemExit(f'bad time expression: {e!r}')
        name, off = m.group(1), float((m.group(2) or '0').replace(' ', ''))
        if name is None: return off
        if name.startswith('line:'): return L[name[5:]]['start'] + off
        if name.startswith('lineend:'): return L[name[8:]]['end'] + off
        if name in extra: return extra[name] + off
        if name not in marks: raise SystemExit(f'unknown mark {name!r} in {e!r}; marks: {", ".join(marks)}')
        return marks[name] + off
    return T
