from pathlib import Path

classification_list = {}


def read_classification(filename="classification.txt"):
    global classification_list

    classification_list.clear()

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_class = ""

    for line in lines:

        line = line.strip().lower()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if line.startswith("class:"):
            current_class = f"temp{len(classification_list)+1}"

            name = line[6:].strip()

            if name:
                current_class = name.title()

            classification_list[current_class] = [[], []]

        elif line.startswith("include:"):

            words = [
                w.strip()
                for w in line[8:].split(",")
                if w.strip()
            ]

            classification_list[current_class][0].extend(words)

        elif line.startswith("exclude:"):

            words = [
                w.strip()
                for w in line[8:].split(",")
                if w.strip()
            ]

            classification_list[current_class][1].extend(words)


def categorize_transaction(description: str) -> str:

    if not classification_list:
        read_classification()

    text = f" {description.lower()} "

    text = (
        text.replace(".", " ")
            .replace("*", " ")
            .replace("-", " ")
    )

    while "  " in text:
        text = text.replace("  ", " ")

    for category, (include_words, exclude_words) in classification_list.items():

        if any(f" {word} " in text for word in exclude_words):
            continue

        if any(f" {word} " in text for word in include_words):
            return category

    return ""

