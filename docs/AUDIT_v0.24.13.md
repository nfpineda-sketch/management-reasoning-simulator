# Deterministic author expansion fix — v0.24.13 (not deployed)

Report 12e177e0dd99464dacbd3de61d7ec722: initial draft omitted explicit bedside
measurements. The paid correction duplicated identical glucose, temperature and
lactate result rows and bindings. 184.091 seconds / 30,154 tokens, no reviewer run.

Compact expansion now fills missing required bedside measurement fields from
existing observable/initial_labs values. Exact duplicate result and binding rows
are collapsed without selecting among conflicting values. Conflicting duplicates
still fail the unchanged compiler gates. No clinical facts or engine parameters
are changed, and no duplicate studies or treatment rules are silently removed.

The attached corrected draft passes compilation after identical-row collapse.
That does not certify clinical coherence: the independent reviewer has not run.
24 offline unittest checks passed, with no paid calls. No actual latency benchmark.
