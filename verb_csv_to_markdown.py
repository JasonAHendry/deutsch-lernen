import re
import sys
import pandas as pd
from dataclasses import dataclass
from typing import Tuple, List


# ================================================================================
# Classes
#
# ================================================================================


@dataclass
class Pronoun:
    pronoun: str
    endung: str


@dataclass
class Verb:
    infinitive: str
    meaning: str
    regular: bool = True
    vokalwechsel: Tuple[str, str] = None
    separable: str = None
    modal: bool = False
    exceptions: List[Tuple[str, str]] = None
    examples: List[str] = None


endungs = {
    "ich": "e",
    "du": "st",
    "Sie": "en",
    "er/sie/es": "t",
    "wir": "en",
    "ihr": "t",
    "sie": "en",
}
pronouns = [Pronoun(p, e) for p, e in endungs.items()]


# ================================================================================
# Functions
#
# ================================================================================


def conjugate(verb: Verb, pronoun: Pronoun) -> str:
    """
    Conjugate for present tense
    
    TODO:
    anhoren - ich hore _ an
    
    """

    stem = re.sub("en$", "", verb.infinitive)
    ending = pronoun.endung

    # Check for stem ending exceptions
    if re.search("[sßz]en$", verb.infinitive) is not None:
        if pronoun.pronoun == "du":
            ending = "t"
    if re.search("[dt]en$", verb.infinitive) is not None:
        if ending in ["t", "st"]:
            ending = f"e{ending}"

    # Check if seperable
    if verb.separable is not None:
        stem = re.sub(f"^{verb.separable}", "", stem)
        ending += f" _ {verb.separable}"

    # Vokalwechsel if necessary
    if verb.vokalwechsel is not None:
        if pronoun.pronoun in ["du", "er/sie/es"]:
            stem = re.sub(verb.vokalwechsel[0], verb.vokalwechsel[1], stem)

    # Handle arbitrary exceptions
    if verb.exceptions is not None:
        for case, conjugation in verb.exceptions:
            if pronoun.pronoun == case:
                return conjugation

    return stem + ending


def get_conjugation_table(verb: Verb):
    """Get a conjugation table"""

    # Define the table
    table = """
            | Person       | Singular | Plural |
            | ------------ | -------- | ------ |
            | 1st          | {ich} | {wir} |
            | 2nd          | {du} | {ihr} |
            | 2nd (formal) | {Sie} | {Sie} |
            | 3rd          | {er/sie/es} | {sie} |
            """

    # Populate and print
    dt = {
        pronoun.pronoun: f"{pronoun.pronoun} {conjugate(verb, pronoun)}"
        for pronoun in pronouns
    }
    return table.format(**dt)


def get_anki_format(verb: Verb):
    """
    Print in a useful format for Anki cards

    """

    anki_format = f"{verb.infinitive} - {verb.meaning}\n\n" f"Regular: {verb.regular}\n"

    if not verb.regular:
        vkl_str = (
            " -> ".join(verb.vokalwechsel) if verb.vokalwechsel is not None else None
        )
        anki_format += f"Vokalwechsel: {vkl_str}\n"
    if verb.modal:
        anki_format += f"{verb.infinitive} is a modal verb.\n"
    if verb.separable:
        anki_format += f"{verb.infinitive} is a seperable verb.\n"
    if verb.exceptions is not None:
        e_str = ", ".join(e[0] for e in verb.exceptions)
        anki_format += f"Has {len(verb.exceptions)} special exceptions: {e_str}.\n"

    anki_format += f"{get_conjugation_table(verb)}\n\n"

    if verb.examples is not None:
        anki_format += "\n".join(verb.examples)
    anki_format += "\n\n"

    return anki_format


def convert_row_to_verb(row: pd.Series) -> Verb:
    """Convert database row to a Verb"""
    
    # Formatters
    def _(input):
        return input
    def format_vokalwechsel(vokalwechsel: str) -> Tuple[str, str]:
        return tuple(vokalwechsel.split("->"))
    def format_exceptions(exceptions: str) -> List[str]: 
        return [tuple(e.strip().split(" ")) for e in exceptions.split(";")]
    def format_examples(examples: str) -> List[str]:
        return [e.strip() for e in examples.split(";")]
    
    # Fields
    fields = {
        'infinitive': _,
        'meaning': _,
        'regular': _,
        'vokalwechsel': format_vokalwechsel,
        'separable': _,
        'modal': _,
        'examples': format_examples,
        'exceptions': format_exceptions
    }

    # Populate
    kwargs = {}
    for k, f in fields.items():
        if pd.isna(row[k]):
            continue
        kwargs[k] = f(row[k])
    
    return Verb(**kwargs)

def load_dataframe_as_verbs(csv: str) -> List[Verb]:
    df = pd.read_csv(csv)
    return [
        convert_row_to_verb(row) for _, row in df.iterrows()
    ]

# --------------------------------------------------------------------------------
# Verb Set
#
# --------------------------------------------------------------------------------


def main(verb_csv: str):
    """
    Conjugate the verb set and write to a file

    """
    verb_md = verb_csv.replace(".csv", ".md")
    verbs = load_dataframe_as_verbs(verb_csv)
    verbs = sorted(verbs, key=lambda x: x.infinitive)
    print(f"Loaded {len(verbs)} verbs from '{verb_csv}'...")
    print(f"  Regular: {sum(verb.regular for verb in verbs)}")
    print(f"  Irregular: {sum(not verb.regular for verb in verbs)}")
    print(f"Converting to markdown: {verb_md}")
    with open(verb_md, "w") as markdown:
        for verb in verbs:
            markdown.write(get_anki_format(verb))
            markdown.write(f"{'-'*80}\n")
    print("Done.")


if __name__ == "__main__":
    main(sys.argv[1])
