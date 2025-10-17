from skip.eeschema import schematic as sch

def _get_ref(sym) -> str:
    """Extract reference from symbol (skip v0.2.5+ API)"""
    if hasattr(sym, 'allReferences') and sym.allReferences:
        ref_obj = sym.allReferences[0]
        return str(ref_obj).split('=')[-1].strip() if '=' in str(ref_obj) else str(ref_obj).strip()
    return None

class SchModel:
    def __init__(self, sch_path: str):
        self.path = sch_path
        self.doc = sch.Schematic(sch_path)

    def refs(self): return [_get_ref(s) for s in self.doc.symbol if _get_ref(s)]
    def nets(self): return [n.name() for n in self.doc.nets()]
