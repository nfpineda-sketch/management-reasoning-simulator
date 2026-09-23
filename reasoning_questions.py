"""The four things an order carries, asked the way a person asks them.

Until 2026-09-23 the held-order screen read as a form: "Working model",
"Expected effect", "Reassessment variables". A resident had to work out what the
application wanted before they could answer it, which is a second task on top of
the clinical one and no part of what is being assessed.

The question is the label now. The help says what the category is and nothing
about this patient: it names no finding the resident did not mention, hints at no
diagnosis, and says nothing about which conduct would be right.

The action is one of the four and is the one that is never asked for here. It is
what puts an order in front of the gate, so it is always already recognised; the
screen shows what was understood and does not invite it to be retyped, because a
field that could change an order would let the follow-up administer a drug.
"""

#: (field, question, help) in the order they are asked.
QUESTIONS = (
    ("working_model", "What do you think is going on?",
     "Your current explanation of the problem and the findings that support it. "
     "You do not need a definitive diagnosis."),
    ("action", "What are you going to do?",
     "The interventions, studies or measures you want to order."),
    ("expected_effect", "What do you expect to happen, or what are you trying to clarify?",
     "The response you anticipate, or the information you expect to obtain to guide management."),
    ("reassessment_target", "What will you check, and when?",
     "The variables or findings you will check, and the moment or condition for doing so."),
)

#: The same four, as a clause that fits inside a sentence about them.
SHORT = {
    "working_model": "what you think is going on",
    "action": "what you want to do",
    "expected_effect": "what you expect to happen",
    "reassessment_target": "what you will check",
    "management_priority": "which problem you are addressing first",
    "reassessment_timing": "when you will check it",
}

HELP = {field: help_text for field, _, help_text in QUESTIONS}
QUESTION = {field: question for field, question, _ in QUESTIONS}

#: Asked only because it is useful to record, never because it holds anything.
OPTIONAL = ("management_priority",)
