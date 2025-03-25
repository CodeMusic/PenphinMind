from redminelib import Redmine
import os

class RedmineManager:
    def __init__(self):
        self.api_key = os.getenv('REDMINE_API_KEY')
        self.url = os.getenv('REDMINE_URL', 'http://localhost:3000')
        self.redmine = Redmine(self.url, key=self.api_key)
        self.project_id = 'penphin-os'

    def log_learning(self, title, description, category="learning"):
        """
        Log a learning event or insight
        """
        return self.redmine.issue.create(
            project_id=self.project_id,
            subject=title,
            description=description,
            tracker_id=1,  # 1 for learning
            category=category
        )

    def log_training_result(self, model_name, accuracy, notes):
        """
        Log training results
        """
        return self.redmine.issue.create(
            project_id=self.project_id,
            subject=f"Training Results: {model_name}",
            description=f"Accuracy: {accuracy}\nNotes: {notes}",
            tracker_id=2  # 2 for training
        )

    def get_learning_history(self, category=None):
        """
        Retrieve learning history
        """
        filters = {'project_id': self.project_id}
        if category:
            filters['category'] = category
        return self.redmine.issue.filter(**filters) 