import csv
import json
from .constants import COURSE_WEIGHTS_PATH, COURSE_MAPPING_PATH


with open(COURSE_MAPPING_PATH, "r", encoding="utf-8") as mapping_file:
    COURSE_MAPPING = json.load(mapping_file)["mapping"]


def normalizeCourseName(course):
    return COURSE_MAPPING.get(course, course)


def readCourseWeights(course):
    course = normalizeCourseName(course)

    with open(COURSE_WEIGHTS_PATH, "r", encoding="utf-8", newline="") as weights_file:
        for row in csv.DictReader(weights_file):
            if row["Curso"] == course:
                return {subject: int(weight) for subject, weight in row.items() if subject != "Curso"}

    return {}
