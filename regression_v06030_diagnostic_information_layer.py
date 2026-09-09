from pathlib import Path
import ast

s = Path('app.py').read_text()
assert 'v0.6.0.30' in s
assert '"type": "pocus"' in s
assert '"type": "lactate"' in s
assert '"type": "basic_labs"' in s
assert 'def pocus_transition' in s
assert 'def lactate_transition' in s
assert 'def basic_labs_transition' in s
assert 'with st.expander("Diagnostics", expanded=True)' in s
assert '"diagnostic_result": "DIAGNOSTIC RESULTS"' in s
# POCUS/lactate/labs are no longer future-only recognized actions.
parser_block = s[s.index('# v0.6.0.30: diagnostic information layer'):s.index('return {\n        "raw_text": text', s.index('# v0.6.0.30: diagnostic information layer'))]
assert '("pocus", "POCUS")' not in parser_block
assert '("lactate", "lactate")' not in parser_block
assert 'future.append("basic laboratory tests")' not in parser_block
# Antibiotics remain recognized but not executable.
assert '("antibiotic", "antibiotics")' in parser_block
print('v0.6.0.30 diagnostic information layer regression passed')
