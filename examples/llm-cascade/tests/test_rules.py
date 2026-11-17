import pytest

from llm_cascade.rules import extract_field


@pytest.mark.parametrize("text, expected", [
    ("We offer visa sponsorship.", "yes"),
    ("Unfortunately we are unable to sponsor work visas for this role.", "no"),
    ("Sponsorship: none.", "no"),
    ("Candidates must already have the right to work in Ireland.", "no"),
    ("You must be authorized to work in the EU without sponsorship.", "no"),
    ("EU Blue Card support is provided.", "yes"),
    ("We build search for shops.", "unknown"),
])
def test_visa(text, expected):
    assert extract_field("visa_sponsorship", text).value == expected


@pytest.mark.parametrize("text", [
    "Relocation support is available.",  # relocation is not visa sponsorship
    "We help international hires with work permits.",  # no pattern: unclear
    "We sponsor visas. We do not sponsor visas.",  # conflict
])
def test_visa_abstains(text):
    assert extract_field("visa_sponsorship", text) is None


@pytest.mark.parametrize("text, expected", [
    ("This is not a remote position.", "onsite"),
    ("Hybrid, three office days per week.", "hybrid"),
    ("Fully remote within Austria.", "remote"),
    ("Position based in our Madrid office.", "onsite"),
    # a weak cue in boilerplate does not block a clear answer
    ("This position is fully remote. Snacks are available in every office.", "remote"),
])
def test_work_mode(text, expected):
    assert extract_field("work_mode", text).value == expected


def test_work_mode_abstains_on_soft_wording():
    assert extract_field("work_mode", "Office-first culture with optional remote Fridays.") is None


@pytest.mark.parametrize("text, expected", [
    ("Fluent German (C1) is required.", "required"),
    ("German is nice to have.", "preferred"),
    ("German language skills are an advantage but not required.", "preferred"),
    ("French required, German a plus.", "preferred"),
    ("Working language is English; German is not required.", "not_required"),
    ("No language requirements.", "not_required"),
])
def test_german(text, expected):
    assert extract_field("german", text).value == expected


def test_german_abstains_on_company_blurb():
    assert extract_field("german", "We are proud to be a German-founded company.") is None


def test_absence_can_be_distrusted():
    text = "Applicants must hold a valid EU work authorization."  # no cue word for the rules
    assert extract_field("visa_sponsorship", text).value == "unknown"
    assert extract_field("visa_sponsorship", text, trust_absence=False) is None
