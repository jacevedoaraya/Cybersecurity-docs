import unicodedata

# Mapeo de caracteres latinos a homóglifos Unicode (caracteres de otros alfabetos visualmente idénticos)
HOMOGLYPHS = {
    'a': ['а', 'à', 'á', 'â', 'ã', 'ä'],
    'e': ['е', 'è', 'é', 'ê', 'ë'],
    'i': ['і', 'ì', 'í', 'î', 'ï'],
    'o': ['о', 'ò', 'ó', 'ô', 'õ', 'ö'],
    'p': ['р'],
    'c': ['с'],
    'x': ['х'],
    'y': ['у'],
}

# Teclas adyacentes en distribución de teclado QWERTY para typosquatting de proximidad
KEYBOARD_ADJACENT = {
    'a': ['q', 'w', 's', 'z'],
    'b': ['v', 'g', 'h', 'n'],
    'c': ['x', 'd', 'f', 'v'],
    'd': ['e', 'r', 'f', 'c', 'x', 's'],
    'e': ['w', 'r', 'd', 's'],
    'f': ['r', 't', 'g', 'v', 'c', 'd'],
    'g': ['t', 'y', 'h', 'b', 'v', 'f'],
    'h': ['y', 'u', 'j', 'n', 'b', 'g'],
    'i': ['u', 'o', 'k', 'j'],
    'l': ['k', 'o', 'p'],
    'm': ['n', 'j', 'k'],
    'o': ['i', 'p', 'l', 'k'],
    'p': ['o', 'l'],
    'q': ['w', 'a'],
    'r': ['e', 't', 'f', 'd'],
    's': ['w', 'e', 'd', 'x', 'z', 'a'],
    't': ['r', 'y', 'g', 'f'],
    'u': ['y', 'i', 'h', 'j'],
    'v': ['c', 'f', 'g', 'b'],
    'w': ['q', 'e', 's'],
    'x': ['z', 's', 'd', 'c'],
    'y': ['t', 'u', 'h', 'g'],
    'z': ['a', 's', 'x']
}

COMMON_TLDS = ['com', 'co', 'net', 'org', 'info', 'biz', 'io', 'security', 'xyz']


class DomainGenerator:
    def __init__(self, domain: str):
        parts = domain.lower().split('.')
        self.name = parts[0]
        self.tld = '.'.join(parts[1:]) if len(parts) > 1 else 'com'

    def generate_all(self) -> set:
        """Genera un conjunto único con todas las variaciones posibles."""
        variants = set()
        
        variants.update(self._omission_variants())
        variants.update(self._repetition_variants())
        variants.update(self._adjacent_key_variants())
        variants.update(self._homoglyph_variants())
        variants.update(self._tld_swap_variants())
        
        # Eliminar el dominio legítimo original
        original = f"{self.name}.{self.tld}"
        variants.discard(original)
        
        return variants

    def _omission_variants(self) -> set:
        """Omisión de un carácter (ej: gmai.com)."""
        res = set()
        for i in range(len(self.name)):
            variant = self.name[:i] + self.name[i+1:]
            if variant:
                res.add(f"{variant}.{self.tld}")
        return res

    def _repetition_variants(self) -> set:
        """Repetición accidental de una letra (ej: gooogle.com)."""
        res = set()
        for i in range(len(self.name)):
            variant = self.name[:i] + self.name[i] + self.name[i:]
            res.add(f"{variant}.{self.tld}")
        return res

    def _adjacent_key_variants(self) -> set:
        """Sustitución por teclas cercanas en el teclado."""
        res = set()
        for i, char in enumerate(self.name):
            if char in KEYBOARD_ADJACENT:
                for adj in KEYBOARD_ADJACENT[char]:
                    variant = self.name[:i] + adj + self.name[i+1:]
                    res.add(f"{variant}.{self.tld}")
        return res

    def _homoglyph_variants(self) -> set:
        """Variaciones con caracteres Unicode confusables (Ataques IDN)."""
        res = set()
        for i, char in enumerate(self.name):
            if char in HOMOGLYPHS:
                for homo in HOMOGLYPHS[char]:
                    variant = self.name[:i] + homo + self.name[i+1:]
                    res.add(f"{variant}.{self.tld}")
        return res

    def _tld_swap_variants(self) -> set:
        """Intercambio de TLDs comunes."""
        res = set()
        for tld in COMMON_TLDS:
            if tld != self.tld:
                res.add(f"{self.name}.{tld}")
        return res


