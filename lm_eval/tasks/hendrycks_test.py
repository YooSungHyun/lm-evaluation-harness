import csv
import random
from lm_eval.base import MultipleChoiceTask
from ..utils import sh
from pathlib import Path

SUBJECTS = ['abstract_algebra', 'anatomy', 'astronomy', 'business_ethics', 'clinical_knowledge', 'college_biology',
            'college_chemistry', 'college_computer_science', 'college_mathematics', 'college_medicine', 'college_physics',
            'computer_security', 'conceptual_physics', 'econometrics', 'electrical_engineering', 'elementary_mathematics',
            'formal_logic', 'global_facts', 'high_school_biology', 'high_school_chemistry', 'high_school_computer_science',
            'high_school_european_history', 'high_school_geography', 'high_school_government_and_politics', 'high_school_macroeconomics',
            'high_school_mathematics', 'high_school_microeconomics', 'high_school_physics', 'high_school_psychology', 'high_school_statistics',
            'high_school_us_history', 'high_school_world_history', 'human_aging', 'human_sexuality', 'international_law', 'jurisprudence',
            'logical_fallacies', 'machine_learning', 'management', 'marketing', 'medical_genetics', 'miscellaneous', 'moral_disputes',
            'moral_scenarios', 'nutrition', 'philosophy', 'prehistory', 'professional_accounting', 'professional_law', 'professional_medicine',
            'professional_psychology', 'public_relations', 'security_studies', 'sociology', 'us_foreign_policy', 'virology', 'world_religions']


def create_all_tasks():
    """Creates a dictionary of tasks from a list of subjects
    :return: {task_name: task}
        e.g. {hendrycksTest-abstract_algebra: Task, hendrycksTest-anatomy: Task}
    """
    return {
        f"hendrycksTest-{sub}": create_task(sub) for sub in SUBJECTS
    }


def create_task(subject):
    class HendrycksTest(GeneralHendrycksTest):
        def __init__(self):
            super().__init__(subject)
    return HendrycksTest


class GeneralHendrycksTest(MultipleChoiceTask):
    DATASET_PATH = Path("data/hendrycksTest/")

    def __init__(self, subject):
        self.subject = subject
        super().__init__()

    def download(self):
        if not self.DATASET_PATH.exists():
            sh("""
                mkdir -p data
                wget https://people.eecs.berkeley.edu/~hendrycks/data.tar -P data/
                tar -xf data/data.tar -C data/
                rm data/data.tar
                mv data/data data/hendrycksTest
                """)

    def has_training_docs(self):
        return True

    def has_validation_docs(self):
        return False

    def has_test_docs(self):
        return True

    def _convert_standard(self, doc):
        return {
            "query": "Question: " + doc[0] + "\nAnswer:",
            "choices": doc[1:5],
            "gold": ['A', 'B', 'C', 'D'].index(doc[5])
        }

    def _load_docs(self, filename):
        reader = csv.reader(open(filename, 'r'), quotechar='"', delimiter=',')
        return (self._convert_standard(doc) for doc in reader)

    def training_docs(self):
        # Use all files in the auxiliary_train, dev, val directories
        # auxiliary_train includes some UnifiedQA MC tasks
        docs = []
        for train_dir in ["auxiliary_train", "dev", "val"]:
            for f in (self.DATASET_PATH / train_dir).iterdir():
                docs.extend(self._load_docs(f))
        return docs

    def validation_docs(self):
        raise NotImplementedError

    def test_docs(self):
        filename = self.DATASET_PATH / "test" / f"{self.subject}_test.csv"
        return self._load_docs(filename)

    def fewshot_examples(self, k):
        assert k <= 5, "Maximum 5 few shot examples."
        filename = self.DATASET_PATH / "dev" / f"{self.subject}_dev.csv"
        return random.sample(list(self._load_docs(filename)), k)

    def fewshot_description(self):
        subject = self.subject.replace("_", " ")
        return f"The following are multiple choice questions (with answers) about {subject}."

    def doc_to_text(self, doc):
        return doc["query"]
