"""PHASE2_AMENDMENT_3: the formal successor stage of PHASE2_AMENDMENT_2 (shadow only).

The historical Phase-2 closure (d2cca46, digest 22b90a6f...), PHASE2_AMENDMENT_1 (digest 10b45ce2..., certified) and
PHASE2_AMENDMENT_2 (digest a0af7d08..., certified) are NOT rewritten here. This stage follows the second amendment the way
that one followed the first: it DECLARES what it inserted into the five common files it changed (``derived.py``,
``state.py``, ``integration.py``, ``provenance.py``, ``decision_pack.py``), so the second amendment's files are rebuilt from
the live ones by reversing those insertions and proven by their SHA; the first amendment's are rebuilt from those by the
second amendment's own declared reversal, and the closure's by the first amendment's. The historical closure and every
stage in between therefore keep reconstructing exactly, and each digest recomputes to the value it was certified at.

What the stage adds to the physiology is ``vascular_support`` (its own file): the common exogenous vasoconstrictor support
and its bounded factor on the common tone target, behind ``CoreProfile.vasoconstrictor_support_to_tone_gain`` (None by
default: every committed behaviour is unchanged bit for bit), and the first writer of that support, a fixed-rate
norepinephrine infusion. It is a development mechanism: no dose-response is calibrated and no value is approved.

The views this module installs (``tree`` / ``chain``) are for the closed packages' test fixtures and for the historical
verification of the closure: they show the tree as the closure left it, by composing this stage's reversal with the two
before it. ``amendment_2_tree`` shows the tree as the SECOND amendment left it, for that amendment's own tests, and
``amendment_1_tree`` as the FIRST left it. They change no behaviour: a view of the source, not of the physiology.

The amended core's own digest lives OUTSIDE this package (the amendment record and the runtime's lineage), because it
covers this file too.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from . import amendment_1 as a1
from . import amendment_2 as a2
from . import calibration as _calibration
from . import derived as _dv
from . import integration as _integration
from . import provenance as _provenance
from . import state as _state
from . import tone_domain as x1

ROOT = a1.ROOT
CORE_DIR = a1.CORE_DIR
REVISION = "PHASE2_AMENDMENT_3"
PREDECESSOR = "PHASE2_AMENDMENT_2"
DECIDED = "2026-11-17"
OWN = ("clinical_core/amendment_3.py", "clinical_core/vascular_support.py")
RECORD = ROOT / "docs" / "revision" / "PHASE2_AMENDMENT_3.json"
#: The certified digests this stage stands on: immutable, named here to be VERIFIED, never to be replaced.
AMENDMENT_2_DIGEST = "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
AMENDMENT_1_DIGEST = a2.AMENDMENT_1_DIGEST
#: What the stage registers, as each stage did: its stage module is not a source of the decision pack.
TUPLES_ADDED = {"PACK_DIGEST_EXCLUDED": ("clinical_core/amendment_3.py",)}
#: The names this stage adds to the live classes, which every earlier tree's view leaves out.
NEW_PROFILE_FIELD = "vasoconstrictor_support_to_tone_gain"
NEW_AUX_FIELD = "vasoconstrictor_support"
NEW_CHANGE_FIELD = "vasoconstriction"
NEW_CONTRIBUTOR_TYPES = ("norepinephrine",)

#: What this stage inserted, as (live text, text before): reversing them in order gives the second amendment's file.
REVERSAL = {'clinical_core/decision_pack.py': (('                        "clinical_core/amendment_1.py", '
                                     '"clinical_core/amendment_2.py",\n'
                                     '                        "clinical_core/amendment_3.py")\n',
                                     '                        "clinical_core/amendment_1.py", '
                                     '"clinical_core/amendment_2.py")\n'),),
 'clinical_core/derived.py': (('    vasodilatory_burden_to_tone_gain: float | None = None\n'
                               '    # PHASE2_AMENDMENT_3: the vasoconstrictor reader of the common tone target, '
                               'UNSET (None) by default. Declared, the\n'
                               "    # target is multiplied by 1 + k u / (1 + u), u the state's common "
                               'vasoconstrictor support: a factor at or above 1,\n'
                               '    # exactly 1 with no support (so the authored arrival pressure stays the scale), '
                               'increasing in the support and\n'
                               '    # bounded by 1 + k. A third independent factor beside the compensation and the '
                               'distributive one: never a volume,\n'
                               "    # never a pump term, never a pressure gain of its own. The core stays T's only "
                               'writer. No value is chosen here.\n'
                               '    vasoconstrictor_support_to_tone_gain: float | None = None\n'
                               '    pressure_levels:',
                               '    vasodilatory_burden_to_tone_gain: float | None = None\n    pressure_levels:'),
                              ('            raise CoreInvariantError("vasodilatory_burden_to_tone_gain is None '
                               '(UNSET: no vasodilatory reader) or a "\n'
                               '                                     "finite positive tone loss per unit of '
                               'burden")\n'
                               '        support = self.vasoconstrictor_support_to_tone_gain\n'
                               '        if support is not None and (isinstance(support, bool) or not '
                               'isinstance(support, (int, float))\n'
                               '                                    or not math.isfinite(support) or support <= '
                               '0.0):\n'
                               '            # PHASE2_AMENDMENT_3: UNSET is None (no reader); declared, the gain is '
                               'finite and positive: the largest\n'
                               '            # fractional rise of the tone target the support can cause. The factor '
                               'is bounded by 1 + k, and the tone\n'
                               '            # domain refuses, before execution, a gain whose largest target would '
                               "reach T's guard.\n"
                               '            raise CoreInvariantError("vasoconstrictor_support_to_tone_gain is None '
                               '(UNSET: no vasoconstrictor "\n'
                               '                                     "reader) or a finite positive largest '
                               'fractional tone rise")\n',
                               '            raise CoreInvariantError("vasodilatory_burden_to_tone_gain is None '
                               '(UNSET: no vasodilatory reader) or a "\n'
                               '                                     "finite positive tone loss per unit of '
                               'burden")\n'),
                              ('    "vasoconstrictor_support_to_tone_gain": (PROVISIONAL, "UNSET '
                               '(PHASE2_AMENDMENT_3): the largest fractional rise of "\n'
                               '                                                          "the common tone target '
                               'that the common vasoconstrictor "\n'
                               '                                                          "support can cause, as the '
                               'bounded factor "\n'
                               '                                                          "1 + k u / (1 + u) on the '
                               'target (1 with no support, so "\n'
                               '                                                          "the arrival tone stays 1 '
                               'exactly); None by default (no "\n'
                               '                                                          "reader); it reads no '
                               'pressure, deficit, D, baroreflex, "\n'
                               '                                                          "volume or pump and is '
                               'never solved from an observed MAP; "\n'
                               '                                                          "a DEVELOPMENT behavioural '
                               'region (LOW / CENTER_REFERENCE "\n'
                               '                                                          "/ HIGH witnesses), never '
                               'a clinical dose-response; not "\n'
                               '                                                          "approved"),\n'
                               '    "systemic_stress_to_sympathetic_gain": (PROVISIONAL, "UNSET (P2V-1): sympathetic '
                               'drive per unit of the common "\n',
                               '    "systemic_stress_to_sympathetic_gain": (PROVISIONAL, "UNSET (P2V-1): sympathetic '
                               'drive per unit of the common "\n'),
                              ('            data["amendment_2"] = data["amendment_2"].to_dict()\n'
                               '        if data.get("vasoconstrictor_support_to_tone_gain") is None:\n'
                               '            # PHASE2_AMENDMENT_3: an UNSET reader is not named, so every profile '
                               'without it travels (and digests)\n'
                               '            # exactly as it did.\n'
                               '            data.pop("vasoconstrictor_support_to_tone_gain", None)\n'
                               '        return data\n',
                               '            data["amendment_2"] = data["amendment_2"].to_dict()\n'
                               '        return data\n'),
                              ('                   / (1.0 + tone_loss * state.aux.vasodilatory_burden))\n'
                               '    support_gain = profile.vasoconstrictor_support_to_tone_gain\n'
                               '    if support_gain is not None:\n'
                               '        # PHASE2_AMENDMENT_3: the vasoconstrictor reader: what an exogenous '
                               'vasoconstrictor adds to the tone the state\n'
                               '        # already calls for, as a bounded factor at or above 1 that is 1 exactly '
                               'with no support (so arrival stays the\n'
                               '        # scale). A third independent factor: it reads no deficit and no burden, '
                               'adds no volume and no pump output,\n'
                               "        # and the core stays T's only writer. UNSET (None) by default.\n"
                               '        from . import vascular_support as _amendment_3\n'
                               '        target *= _amendment_3.tone_factor(state.aux.vasoconstrictor_support, '
                               'support_gain)\n'
                               '    return target\n',
                               '                   / (1.0 + tone_loss * state.aux.vasodilatory_burden))\n'
                               '    return target\n')),
 'clinical_core/integration.py': (('                         SystemicStressChange, VasodilationChange, '
                                   'VasoconstrictionChange)\n',
                                   '                         SystemicStressChange, VasodilationChange)\n'),
                                  ('    vasodilation: tuple[VasodilationChange, ...] = ()  # changes to the common '
                                   'vasodilatory burden this minute (P2W-1)\n'
                                   '    vasoconstriction: tuple[VasoconstrictionChange, ...] = ()  # changes to the '
                                   'common vasoconstrictor support (PHASE2_AMENDMENT_3)\n',
                                   '    vasodilation: tuple[VasodilationChange, ...] = ()  # changes to the common '
                                   'vasodilatory burden this minute (P2W-1)\n'),
                                  ('    from . import interventions, logistics, modules, vascular_support  # noqa: '
                                   'F401\n',
                                   '    from . import interventions, logistics, modules  # noqa: F401\n'),
                                  ('    recovery_max = 1.0 if loss is None else 1.0 + loss * '
                                   'anchors.arrival_vasodilatory_burden\n'
                                   '    # PHASE2_AMENDMENT_3: the vasoconstrictor factor is below 1 + k whatever the '
                                   'support, so 1 + k scales the largest\n'
                                   "    # reachable target and the loop's slope bound the way the distributive "
                                   'recovery does (1 exactly while UNSET).\n'
                                   '    support_max = 1.0 if profile.vasoconstrictor_support_to_tone_gain is None '
                                   '\\\n'
                                   '        else 1.0 + profile.vasoconstrictor_support_to_tone_gain\n',
                                   '    recovery_max = 1.0 if loss is None else 1.0 + loss * '
                                   'anchors.arrival_vasodilatory_burden\n'),
                                  ('            "largest_target": (1.0 + gain) / normalization * recovery_max * '
                                   'support_max,\n',
                                   '            "largest_target": (1.0 + gain) / normalization * recovery_max,\n'),
                                  ('        # PHASE2_AMENDMENT_3: the refusal names the third factor when it is '
                                   'declared (the text is unchanged while UNSET).\n'
                                   '        ceiling = "" if profile.vasoconstrictor_support_to_tone_gain is None '
                                   'else \\\n'
                                   '            f" times the vasoconstrictor ceiling {1.0 + '
                                   'profile.vasoconstrictor_support_to_tone_gain!r}"\n'
                                   '        raise CoreInvariantError(\n'
                                   '            f"the tone target\'s largest reachable value '
                                   '{domain[\'largest_target\']!r} (the compensation\'s "\n'
                                   '            f"{domain[\'compensation_max\']!r} times the distributive recovery '
                                   '{domain[\'recovery_max\']!r}{ceiling}) reaches "\n',
                                   '        raise CoreInvariantError(\n'
                                   '            f"the tone target\'s largest reachable value '
                                   '{domain[\'largest_target\']!r} (the compensation\'s "\n'
                                   '            f"{domain[\'compensation_max\']!r} times the distributive recovery '
                                   '{domain[\'recovery_max\']!r}) reaches "\n'),
                                  ('            "loop_slope_bound": recovery_max * support_max * gain * sensitivity '
                                   '* afterload_at_the_lower_end / normalization,\n',
                                   '            "loop_slope_bound": recovery_max * gain * sensitivity * '
                                   'afterload_at_the_lower_end / normalization,\n'),
                                  ('    if domain["distributive_reader"] or '
                                   'profile.vasoconstrictor_support_to_tone_gain is not None:\n'
                                   '        if domain["loop_slope_bound"] >= 1.0:\n',
                                   '    if domain["distributive_reader"]:\n'
                                   '        if domain["loop_slope_bound"] >= 1.0:\n'),
                                  ('        raise ProvenanceError(f"{contributor.source.key}: the vasodilatory '
                                   'burden changes only by a tuple of "\n'
                                   '                              "VasodilationChange records")\n'
                                   '    if not isinstance(contribution.vasoconstriction, tuple) or any(not '
                                   'isinstance(item, VasoconstrictionChange)\n'
                                   '                                                                   for item in '
                                   'contribution.vasoconstriction):\n'
                                   '        raise ProvenanceError(f"{contributor.source.key}: the vasoconstrictor '
                                   'support changes only by a tuple of "\n'
                                   '                              "VasoconstrictionChange records")\n',
                                   '        raise ProvenanceError(f"{contributor.source.key}: the vasodilatory '
                                   'burden changes only by a tuple of "\n'
                                   '                              "VasodilationChange records")\n'),
                                  ('                 + contribution.availability + contribution.systemic_stress + '
                                   'contribution.vasodilation\n'
                                   '                 + contribution.vasoconstriction):\n',
                                   '                 + contribution.availability + contribution.systemic_stress + '
                                   'contribution.vasodilation):\n'),
                                  ('    availability, systemic_stress, vasodilation, vasoconstriction = [], [], [], '
                                   '[]\n',
                                   '    availability, systemic_stress, vasodilation = [], [], []\n'),
                                  ('        vasodilation.extend(contribution.vasodilation)\n'
                                   '        vasoconstriction.extend(contribution.vasoconstriction)\n',
                                   '        vasodilation.extend(contribution.vasodilation)\n'),
                                  ('    if profile.deficit_to_tone_gain > 0.0 or '
                                   'profile.vasodilatory_burden_to_tone_gain is not None \\\n'
                                   '            or profile.vasoconstrictor_support_to_tone_gain is not None:\n',
                                   '    if profile.deficit_to_tone_gain > 0.0 or '
                                   'profile.vasodilatory_burden_to_tone_gain is not None:\n'),
                                  ('                         '
                                   'systemic_encephalopathy_burden=_systemic_burden_after(state, anchors, profile),\n'
                                   '                         vasoconstrictor_support=_vasoconstriction_after(state, '
                                   'vasoconstriction, profile, minute))\n',
                                   '                         '
                                   'systemic_encephalopathy_burden=_systemic_burden_after(state, anchors, '
                                   'profile))\n'),
                                  ('                          systemic_stress=tuple(systemic_stress), '
                                   'vasodilation=tuple(vasodilation),\n'
                                   '                          vasoconstriction=tuple(vasoconstriction))\n',
                                   '                          systemic_stress=tuple(systemic_stress), '
                                   'vasodilation=tuple(vasodilation))\n'),
                                  ('def _vasoconstriction_after(state: CoreState, vasoconstriction: list, profile: '
                                   'CoreProfile,\n'
                                   '                            minute: int) -> float | None:\n'
                                   '    """PHASE2_AMENDMENT_3: the vasoconstrictor support after the minute: the '
                                   'value it starts with (0 before any writer)\n'
                                   "    plus the minute's changes, summed once by P2T-1A's rule (``distress_sum``). "
                                   'None (not tracked) while its reader is\n'
                                   '    UNSET, and then a change is refused, because nothing would read it, and so '
                                   'is a state that already carries a\n'
                                   '    support (it would be dropped in silence); a minute that would take it '
                                   'materially below 0, or whose changes do not\n'
                                   '    sum to a finite value, is refused, never held. The core adds no kinetics and '
                                   'no coupling of its own."""\n'
                                   '    if profile.vasoconstrictor_support_to_tone_gain is None:\n'
                                   '        if vasoconstriction:\n'
                                   '            raise ProvenanceError(f"minute {minute}: '
                                   '{vasoconstriction[0].source.key} changed the vasoconstrictor "\n'
                                   '                                  "support while its reader is UNSET '
                                   '(PHASE2_AMENDMENT_3): nothing would read it")\n'
                                   '        if state.aux.vasoconstrictor_support:\n'
                                   '            raise ProvenanceError(f"minute {minute}: the state carries a '
                                   'vasoconstrictor support of "\n'
                                   '                                  f"{state.aux.vasoconstrictor_support!r} while '
                                   'its reader is UNSET (PHASE2_AMENDMENT_3): "\n'
                                   '                                  "it would be dropped in silence")\n'
                                   '        return None\n'
                                   '    try:\n'
                                   '        value = distress_sum(state.aux.vasoconstrictor_support or 0.0, '
                                   '[item.amount for item in vasoconstriction])\n'
                                   '    except OverflowError:\n'
                                   '        raise ProvenanceError(f"minute {minute}: the vasoconstriction changes do '
                                   'not sum to a finite support "\n'
                                   '                              "(PHASE2_AMENDMENT_3)") from None\n'
                                   '    if value < 0.0:\n'
                                   '        raise ProvenanceError(f"minute {minute}: the vasoconstriction changes '
                                   'take the support to {value!r}, below 0 "\n'
                                   '                              "(PHASE2_AMENDMENT_3)")\n'
                                   '    return value\n'
                                   '\n'
                                   '\n'
                                   'def _systemic_stress_after(state: CoreState, stress: list, profile: CoreProfile, '
                                   'minute: int) -> float:\n',
                                   'def _systemic_stress_after(state: CoreState, stress: list, profile: CoreProfile, '
                                   'minute: int) -> float:\n'),
                                  ('        raise ProvenanceError("the vasodilatory burden changed by other than its '
                                   'recorded changes")\n'
                                   '    if (after.aux.vasoconstrictor_support or 0.0) != '
                                   'distress_sum(before.aux.vasoconstrictor_support or 0.0,\n'
                                   '                                                                  [item.amount '
                                   'for item in record.vasoconstriction]):\n'
                                   '        # PHASE2_AMENDMENT_3: the vasoconstrictor support moves by exactly the '
                                   "minute's recorded changes, never\n"
                                   '        # otherwise (not tracked reads as none: an untracked state and a support '
                                   'of 0 are the same state).\n'
                                   '        raise ProvenanceError("the vasoconstrictor support changed by other than '
                                   'its recorded changes")\n',
                                   '        raise ProvenanceError("the vasodilatory burden changed by other than its '
                                   'recorded changes")\n'),
                                  ('            # PHASE2_AMENDMENT_3: the refusal names the factor that is declared '
                                   '(unchanged with the distributive reader alone).\n'
                                   '            named = "the distributive factor" if domain["distributive_reader"] '
                                   'else "the vasoconstrictor ceiling"\n'
                                   '            if domain["distributive_reader"] and '
                                   'profile.vasoconstrictor_support_to_tone_gain is not None:\n'
                                   '                named = "the distributive factor and the vasoconstrictor '
                                   'ceiling"\n'
                                   '            raise CoreInvariantError(\n'
                                   '                f"the tone loop\'s derived bound with {named}, '
                                   '{domain[\'loop_slope_bound\']!r}, is not "\n',
                                   '            raise CoreInvariantError(\n'
                                   '                f"the tone loop\'s derived bound with the distributive factor, '
                                   '{domain[\'loop_slope_bound\']!r}, is not "\n')),
 'clinical_core/provenance.py': (('@dataclass(frozen=True)\n'
                                  'class VasoconstrictionChange:\n'
                                  '    """PHASE2_AMENDMENT_3: one source\'s change to the common vasoconstrictor '
                                  'support in one minute.\n'
                                  '\n'
                                  '    The amount adds to the support the minute starts with (finite; 0 changes '
                                  'nothing), as a vasodilation change adds to\n'
                                  '    the burden: the support stays where its writers leave it, and the core adds '
                                  'no kinetics of its own (a writer brings\n'
                                  '    its own onset and offset). The support is a common input, never a drug term '
                                  'in the tone equation: a writer declares\n'
                                  '    what its own mechanism (a vasopressor infusion first; later another '
                                  'vasopressor or an endogenous vasoconstrictive\n'
                                  '    state) does to it, and the core only sums the changes. It is NOT a negative '
                                  'vasodilatory burden (P2X-1, FACULTY\n'
                                  '    DECISIONS 2 and 5): the two are separate inputs with separate readers. A '
                                  'minute whose changes would take the\n'
                                  '    support below 0 is refused; with its reader UNSET a change is refused, '
                                  'because nothing would read it. The channel T\n'
                                  "    keeps exactly one writer, the core's tone response.\n"
                                  '\n'
                                  "    WRITER CONTRACT, binding on every writer, as P2X-1's is on the burden: the "
                                  'amount may NOT be computed from the\n'
                                  '    current MAP, pressure_rel, T, the relative output or delivery, the capillary '
                                  'refill or the sympathetic drive (no\n'
                                  '    closed pressure -> support -> T -> pressure loop is authorized, and a '
                                  'titration engine is not part of this stage).\n'
                                  "    A writer's allowed inputs are its own order, time and its own declared "
                                  'mechanism. It never writes V or Hb (a\n'
                                  '    vasoconstrictor adds no volume) and never writes P (it creates no pump '
                                  'output).\n'
                                  '    """\n'
                                  '\n'
                                  '    amount: float\n'
                                  '    source: Source\n'
                                  '    minute: int\n'
                                  '    description: str\n'
                                  '\n'
                                  '    def __post_init__(self):\n'
                                  '        if isinstance(self.amount, bool) or not isinstance(self.amount, (int, '
                                  'float)) \\\n'
                                  '                or not math.isfinite(self.amount):\n'
                                  '            raise ProvenanceError(f"a vasoconstriction change is a finite number, '
                                  'not {self.amount!r}")\n'
                                  '        object.__setattr__(self, "amount", float(self.amount))\n'
                                  '        if not isinstance(self.source, Source):\n'
                                  '            raise ProvenanceError("every vasoconstriction change names its '
                                  'Source")\n'
                                  '        _minute(self.minute)\n'
                                  '        _description(self.description)\n'
                                  '\n'
                                  '    def to_dict(self) -> dict:\n'
                                  '        return {"type": "vasoconstriction", "amount": self.amount, "source": '
                                  'self.source.to_dict(),\n'
                                  '                "minute": self.minute, "description": self.description}\n'
                                  '\n'
                                  '\n'
                                  '@dataclass(frozen=True)\n'
                                  'class AvailabilityChange:\n',
                                  '@dataclass(frozen=True)\nclass AvailabilityChange:\n'),
                                 ('    vasodilation: tuple[VasodilationChange, ...] = field(default=())\n'
                                  '    # PHASE2_AMENDMENT_3: empty in every minute no writer changed the '
                                  'vasoconstrictor support, and then not serialized.\n'
                                  '    vasoconstriction: tuple[VasoconstrictionChange, ...] = field(default=())\n',
                                  '    vasodilation: tuple[VasodilationChange, ...] = field(default=())\n'),
                                 ('                     + self.vasodilation + self.vasoconstriction):\n',
                                  '                     + self.vasodilation):\n'),
                                 ('        data = {"minute": self.minute, "deltas": [item.to_dict() for item in '
                                  'self.deltas],\n',
                                  '        return {"minute": self.minute, "deltas": [item.to_dict() for item in '
                                  'self.deltas],\n'),
                                 ('                "vasodilation": [item.to_dict() for item in self.vasodilation]}\n'
                                  '        if self.vasoconstriction:\n'
                                  '            # PHASE2_AMENDMENT_3: named only where a writer changed the support, '
                                  'so every record without one serializes\n'
                                  '            # (and digests) exactly as it did.\n'
                                  '            data["vasoconstriction"] = [item.to_dict() for item in '
                                  'self.vasoconstriction]\n'
                                  '        return data\n',
                                  '                "vasodilation": [item.to_dict() for item in '
                                  'self.vasodilation]}\n')),
 'clinical_core/state.py': (('    systemic_encephalopathy_burden: float | None = None\n'
                             '    # PHASE2_AMENDMENT_3: the common exogenous vasoconstrictor support, at or above 0 '
                             '(0 none), in half-maximal units of\n'
                             '    # its tone effect. None is NOT TRACKED (every profile whose reader is UNSET), and '
                             'then the state serializes exactly\n'
                             '    # as it did: this field is not one of AUXILIARY_FIELDS. It is not T (the core '
                             "stays T's only writer), not the\n"
                             '    # vasodilatory burden with its sign changed, not volume and not pump; only '
                             'vasoconstriction changes write it.\n'
                             '    vasoconstrictor_support: float | None = None\n'
                             '\n'
                             '    def __post_init__(self):\n',
                             '    systemic_encephalopathy_burden: float | None = None\n'
                             '\n'
                             '    def __post_init__(self):\n'),
                            ('                raise CoreInvariantError("the systemic encephalopathy burden is a '
                             'share between 0 and 1")\n'
                             '        if self.vasoconstrictor_support is not None:\n'
                             '            _finite(self.vasoconstrictor_support, "vasoconstrictor_support")\n'
                             '            if self.vasoconstrictor_support < 0.0:\n'
                             '                raise CoreInvariantError("the vasoconstrictor support is never '
                             'negative")\n',
                             '                raise CoreInvariantError("the systemic encephalopathy burden is a '
                             'share between 0 and 1")\n'),
                            ('            data["systemic_encephalopathy_burden"] = '
                             'self.systemic_encephalopathy_burden\n'
                             '        if self.vasoconstrictor_support is not None:\n'
                             '            data["vasoconstrictor_support"] = self.vasoconstrictor_support\n'
                             '        return data\n',
                             '            data["systemic_encephalopathy_burden"] = '
                             'self.systemic_encephalopathy_burden\n'
                             '        return data\n'),
                            ('        optional = {"systemic_encephalopathy_burden", "vasoconstrictor_support"}\n',
                             '        optional = {"systemic_encephalopathy_burden"}\n'))}
CORE_AT_AMENDMENT_2 = {'clinical_core/decision_pack.py': '0faaa3d1b18977bc138be38906f83c76b5a6c1117465c552610f30ee5e6fa519',
 'clinical_core/derived.py': 'b0cef174783f463ab52353790226cd2f44c917237264b771c1ab1714c9c32465',
 'clinical_core/integration.py': 'c526ed18588cdea0360ef9261ceadf3edad57d70842930046fd0ca28b6842d8c',
 'clinical_core/provenance.py': '40ed2f08456ecefea5aafc1f895a3df962a00d0bba7edc54243fb574a2ef5af8',
 'clinical_core/state.py': '161cffa8a3e7f9a37acc5fd6468e7af8fa1d8d9bba4c7b1f47a80666b3552cc4'}

#: Files this stage changed that the second amendment did not: their second-amendment text IS the first amendment's.
NEW_COMMON = tuple(sorted(set(REVERSAL) - set(a2.REVERSAL)))

# The two earlier stages as they are at import, before any view replaces a name of theirs.
_REAL_LIVE_CORE_SOURCES = a2._A1_LIVE_CORE_SOURCES
_A1_REVERSAL = a1.REVERSAL
_A2_REVERSAL = a2.REVERSAL
_A2_CORE_AT_AMENDMENT_1 = a2.CORE_AT_AMENDMENT_1
_A2_OWN = a2.OWN
_A2_NAMES = a2._NAMES
_A2_AUX_NAMES = a2._AUX_NAMES
_PROFILE_FIELDS = _dv.CoreProfile.__dataclass_fields__
_CONTRIBUTION_FIELDS = _integration.Contribution.__dataclass_fields__
_RECORD_FIELDS = _provenance.MinuteRecord.__dataclass_fields__


def _live_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _live(relative: str) -> str:
    """Indirect on purpose, as in every stage: a probe replaces this to mutate a protected source."""
    return _live_text(relative)


def _reverse(relative: str, text: str) -> tuple[str, list]:
    problems = []
    for live, before in REVERSAL[relative]:
        if text.count(live) != 1:
            problems.append(f"{relative}: a declared replacement occurs {text.count(live)} times")
            continue
        text = text.replace(live, before)
    return text, problems


def proved(relative: str, text: str | None = None) -> bool:
    back, problems = _reverse(relative, _live(relative) if text is None else text)
    return not problems and hashlib.sha256(back.encode("utf-8")).hexdigest() == CORE_AT_AMENDMENT_2[relative]


def proofs() -> dict:
    return {relative: proved(relative) for relative in REVERSAL}


def a2_text(relative: str) -> str:
    """The second amendment's file: the live one with this stage's declared insertions reversed (proven)."""
    if relative in REVERSAL:
        if not proved(relative):
            raise AssertionError(f"{relative} is not the second amendment's file plus PHASE2_AMENDMENT_3's insertions")
        return _reverse(relative, _live(relative))[0]
    return _live(relative)


def a2_bytes(relative: str) -> bytes:
    return a2_text(relative).encode("utf-8") if relative in REVERSAL else (ROOT / relative).read_bytes()


def a2_sources(sources: dict) -> dict:
    """A ``path -> sha256`` map of the live package, as the SECOND amendment's tree would hold it."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in CORE_AT_AMENDMENT_2.items():
        if relative in out and proved(relative):
            out[relative] = sha
    return out


def live_core_sources() -> dict:
    return _REAL_LIVE_CORE_SOURCES()


def amended_core_digest_now() -> str:
    """The digest of the amended tree, this stage's files included. Its certified value is recorded outside the package."""
    return a1.core_digest(live_core_sources())


def amendment_2_digest_now() -> str:
    """The SECOND amendment's digest RECOMPUTED from the live tree by reversing this stage's declared insertions. It equals
    AMENDMENT_2_DIGEST only while the reversal is exact and nothing else in the package moved."""
    return a1.core_digest(a2_sources(live_core_sources()))


def _a2_view() -> tuple[dict, dict]:
    """The second amendment's declared reversal widened to the files this stage changed and that one did not: their
    reversal to the first amendment is empty (the second amendment did not touch them) and their first-amendment SHA is
    therefore their second-amendment one."""
    reversal, shas = dict(_A2_REVERSAL), dict(_A2_CORE_AT_AMENDMENT_1)
    for relative in NEW_COMMON:
        reversal[relative] = ()
        shas[relative] = CORE_AT_AMENDMENT_2[relative]
    return reversal, shas


def _install_a2_functions(patch) -> None:
    """The second amendment's own functions reading the SECOND amendment's tree: its text (``a2_text``), its source map, its
    widened reversal and its listings without this stage's files. Everything that stage then does to the first amendment
    and to the closure composes on top of this, unchanged."""
    reversal, shas = _a2_view()
    patch.setattr(a2, "_live", a2_text)
    patch.setattr(a2, "_live_text", a2_text)
    patch.setattr(a2, "_A1_LIVE_CORE_SOURCES", lambda: a2_sources(_REAL_LIVE_CORE_SOURCES()))
    patch.setattr(a2, "REVERSAL", reversal)
    patch.setattr(a2, "CORE_AT_AMENDMENT_1", shas)
    patch.setattr(a2, "NEW_COMMON", tuple(sorted(set(reversal) - set(_A1_REVERSAL))))
    patch.setattr(a2, "OWN", tuple(_A2_OWN) + OWN)


def _a1_bytes_on_the_a2_tree(relative: str) -> bytes:
    """The second amendment's ``a1_bytes`` on ITS tree: a file it did not change is read as that tree holds it."""
    return a2.a1_text(relative).encode("utf-8") if relative in a2.REVERSAL else a2_bytes(relative)


def _a1_common_untouched_on_the_a2_tree() -> dict:
    """The first amendment's ``common_untouched`` on the second amendment's tree: every other source of the closure, as
    that tree holds it (the files this stage changed are read with its insertions reversed)."""
    return {relative: hashlib.sha256(a2_bytes(relative)).hexdigest() == sha
            for relative, sha in a1.closure_sources().items() if relative not in a1.REVERSAL}


def _install_a2_tree(patch) -> None:
    """The second amendment's own functions reading ITS tree with NOTHING of its declarations widened: what that
    amendment's own tests assert about its reversal, its files and its digest stays exactly what it declared."""
    patch.setattr(a2, "_live", a2_text)
    patch.setattr(a2, "_live_text", a2_text)
    patch.setattr(a2, "_A1_LIVE_CORE_SOURCES", lambda: a2_sources(_REAL_LIVE_CORE_SOURCES()))
    patch.setattr(a2, "_A1_COMMON_UNTOUCHED", _a1_common_untouched_on_the_a2_tree)
    patch.setattr(a2, "a1_bytes", _a1_bytes_on_the_a2_tree)


def a1_text(relative: str) -> str:
    """The FIRST amendment's file: the live one through this stage's declared reversal and then the second amendment's."""
    patcher = x1._Patcher()
    try:
        _install_a2_tree(patcher)
        return a2.a1_text(relative)
    finally:
        patcher.restore()


def closure_sources_of(sources: dict) -> dict:
    """The closure's sources rebuilt from a dict of the LIVE sources' hashes, through the three declared reversals."""
    patcher = x1._Patcher()
    try:
        _install_a2_functions(patcher)
        return a2.closure_sources_of(a2_sources(sources))
    finally:
        patcher.restore()


def historical_closure_verifies() -> dict:
    """The four things that together mean the historical closure still stands under this stage. It answers, and never
    raises, with the same keys the runtime's lineage gate reads from every successor."""
    patcher = x1._Patcher()
    try:
        own = proofs()
        _install_a2_functions(patcher)
        standing = a2.historical_closure_verifies()
    except Exception:
        return {"reversal_proven": False, "common_untouched": False, "touched": [], "closure_digest_recomputes": False,
                "closure_record_states_it": False}
    finally:
        patcher.restore()
    return {"reversal_proven": all(own.values()) and bool(standing["reversal_proven"]),
            "common_untouched": bool(standing["common_untouched"]),
            "touched": list(standing["touched"]),
            "closure_digest_recomputes": bool(standing["closure_digest_recomputes"]),
            "closure_record_states_it": bool(standing["closure_record_states_it"])}


def historical_closure_digest_now() -> str:
    """The closure digest RECOMPUTED from the live tree through the three reversals."""
    patcher = x1._Patcher()
    try:
        _install_a2_functions(patcher)
        return a2.historical_closure_digest_now()
    finally:
        patcher.restore()


def amendment_2_verifies() -> dict:
    """The second amendment stands under this stage: its digest recomputes to the certified value and this stage's
    declared reversal rebuilds its files exactly."""
    try:
        digest = amendment_2_digest_now()
        proven = all(proofs().values())
    except Exception:
        return {"digest_recomputes": False, "reversal_proven": False}
    return {"digest_recomputes": digest == AMENDMENT_2_DIGEST, "reversal_proven": proven}


def amendment_1_verifies() -> dict:
    """The first amendment stands under this stage: its digest recomputes from the second amendment's tree, which this
    stage rebuilds, and the second amendment's own declared reversal still rebuilds it."""
    patcher = x1._Patcher()
    try:
        _install_a2_functions(patcher)
        return dict(a2.amendment_1_verifies())
    except Exception:
        return {"digest_recomputes": False, "reversal_proven": False}
    finally:
        patcher.restore()


# The views for the closed packages and for the two earlier amendments' own tests ----------------------------------------

def _lists_the_third_name(module) -> bool:
    held = getattr(module, "PARAMETERS", None)
    return (isinstance(held, dict) and NEW_PROFILE_FIELD in held
            and str(getattr(module, "__name__", "")).startswith("clinical_core"))


def _hide_the_change_field(patch) -> None:
    """The contribution, the minute record and the contributor registry as the earlier trees had them: without this
    stage's change and without its writer."""
    patch.setattr(_integration.Contribution, "__dataclass_fields__",
                  {k: v for k, v in _CONTRIBUTION_FIELDS.items() if k != NEW_CHANGE_FIELD})
    patch.setattr(_provenance.MinuteRecord, "__dataclass_fields__",
                  {k: v for k, v in _RECORD_FIELDS.items() if k != NEW_CHANGE_FIELD})
    patch.setattr(_integration, "_REGISTRY",
                  {k: v for k, v in _integration._REGISTRY.items() if k not in NEW_CONTRIBUTOR_TYPES})


def _widen_a2_view(patch) -> None:
    """Everything the second amendment's own view needs to read THROUGH this stage: its tree, and the listings of the
    profile, the auxiliary state, the contribution and the record without this stage's names too."""
    _install_a2_functions(patch)
    patch.setattr(a2, "_NAMES", tuple(_A2_NAMES) + (NEW_PROFILE_FIELD,))
    patch.setattr(a2, "_AUX_NAMES", tuple(_A2_AUX_NAMES) + (NEW_AUX_FIELD,))
    _hide_the_change_field(patch)


def chain(patch) -> None:
    """For the closed packages' test fixtures: the Phase-2 closure's view, as the two earlier amendments install it, read
    through this stage (the closure text of every file any amendment changed, the registry and the fields without any
    amendment's name, and every closed listing of clinical_core without any amendment's files)."""
    _widen_a2_view(patch)
    a2.chain(patch)


def tree(patch) -> None:
    """The whole closure tree for the closed packages' own analysis and tests, read through this stage."""
    _widen_a2_view(patch)
    a2.tree(patch)


class closure_view:
    """The whole closure tree while a historical verification runs, outside a test (no monkeypatch there)."""

    def __enter__(self):
        self.patch = x1._Patcher()
        try:
            tree(self.patch)
        except BaseException:
            self.patch.restore()
            raise
        return self

    def __exit__(self, *exc):
        self.patch.restore()
        return False


class _A2File:
    """A file this stage changed, as the SECOND amendment left it, for an audit that reads it by path."""

    def __init__(self, relative):
        self.relative = relative

    def read_text(self, encoding="utf-8"):
        return a2_text(self.relative)

    def read_bytes(self):
        return a2_bytes(self.relative)

    def relative_to(self, other):
        return (ROOT / self.relative).relative_to(other)

    def __getattr__(self, name):
        return getattr(ROOT / self.relative, name)

    def __fspath__(self):
        return str(ROOT / self.relative)


class _A2Dir:
    """The repository or package directory as the second amendment left it: its text of the files this stage changed, and
    its listings without this stage's own files."""

    def __init__(self, path=CORE_DIR):
        self.path = path

    def __truediv__(self, name):
        target = self.path / name
        relative = target.relative_to(ROOT).as_posix() if ROOT in target.parents or target == ROOT else None
        if relative in REVERSAL:
            return _A2File(relative)
        return _A2Dir(target) if target.is_dir() else target

    def _listing(self, paths):
        return iter([p for p in paths if p.relative_to(ROOT).as_posix() not in OWN])

    def glob(self, pattern):
        return self._listing(sorted(self.path.glob(pattern)))

    def rglob(self, pattern):
        return self._listing(sorted(self.path.rglob(pattern)))

    def __getattr__(self, name):
        return getattr(self.path, name)

    def __fspath__(self):
        return str(self.path)

    def __str__(self):
        return str(self.path)


def _without_the_third_names(patch, profile_fields) -> None:
    """The profile's field list, every clinical_core parameter registry and every closed snapshot of it, and the auxiliary
    state, the contribution and the record, without this stage's names."""
    patch.setattr(_dv.CoreProfile, "__dataclass_fields__",
                  {k: v for k, v in profile_fields.items() if k != NEW_PROFILE_FIELD})
    for module in [m for m in list(a1.sys.modules.values()) if _lists_the_third_name(m)]:
        patch.setattr(module, "PARAMETERS", {k: v for k, v in module.PARAMETERS.items() if k != NEW_PROFILE_FIELD})
    for module_name, attribute in a1.CLOSED_SNAPSHOTS:
        module = __import__(f"clinical_core.{module_name}", fromlist=[attribute])
        patch.setattr(module, attribute, {k: v for k, v in getattr(module, attribute).items() if k != NEW_PROFILE_FIELD})
    _hide_the_change_field(patch)


def amendment_2_tree(patch) -> None:
    """The tree as the SECOND amendment left it, for that amendment's own tests: its files by text and by path, its
    digest by its own definition, its listings without this stage's files, and its shape (the second amendment's profile
    field and memory are there, this stage's are not)."""
    _install_a2_tree(patch)
    for module in a1._imported_closed_modules() + [_calibration, a1.bf]:
        for attribute in a1._PATH_ATTRIBUTES:
            value = getattr(module, attribute, None)
            if isinstance(value, Path):
                patch.setattr(module, attribute, _A2Dir(value))
    _without_the_third_names(patch, _dv.CoreProfile.__dataclass_fields__)
    aux_fields = _state.AuxiliaryState.__dataclass_fields__
    patch.setattr(_state.AuxiliaryState, "__dataclass_fields__", {k: v for k, v in aux_fields.items() if k != NEW_AUX_FIELD})


def amendment_1_tree(patch) -> None:
    """The tree as the FIRST amendment left it, for that amendment's own tests, read through this stage: the second
    amendment's own view of it, on the second amendment's tree, without this stage's names either."""
    _install_a2_functions(patch)
    patch.setattr(a2, "_AUX_NAMES", tuple(_A2_AUX_NAMES) + (NEW_AUX_FIELD,))
    a2.amendment_1_tree(patch)
    _without_the_third_names(patch, _dv.CoreProfile.__dataclass_fields__)


def non_regression() -> dict:
    """Both earlier amendments reproduce on their own trees, the historical closure recomputes, and nothing else moved."""
    standing = historical_closure_verifies()
    second, first = amendment_2_verifies(), amendment_1_verifies()
    return {"amendment_2": second, "amendment_1": first, "historical_closure": standing,
            "pass": second["digest_recomputes"] and second["reversal_proven"] and first["digest_recomputes"]
            and first["reversal_proven"] and standing["reversal_proven"] and standing["common_untouched"]
            and standing["closure_digest_recomputes"] and standing["closure_record_states_it"]}
