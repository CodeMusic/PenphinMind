"""
Neurological Function:
    Redmine Manager System:
    - Learning logging
    - Training logging
    - History tracking
    - Error handling
    - State management
    - Feedback processing

Project Function:
    Handles Redmine integration:
    - Learning event logging
    - Training result logging
    - History retrieval
    - Error handling
"""

from redminelib import Redmine
import os
from ..FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from typing import Any, Optional

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class RedmineManager:
    """Manages Redmine integration for learning and training logging"""
    
    def __init__(self):
        """Initialize Redmine manager"""
        journaling_manager.recordScope("RedmineManager.__init__")
        try:
            self.api_key = os.getenv('REDMINE_API_KEY')
            self.url = os.getenv('REDMINE_URL', 'http://localhost:3000')
            self.redmine = Redmine(self.url, key=self.api_key)
            self.project_id = 'penphin-os'
            journaling_manager.recordDebug(f"Redmine manager initialized with URL: {self.url}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing Redmine manager: {e}")
            raise

    def log_learning(self, title: str, description: str, category: str = "learning") -> Any:
        """Log a learning event or insight"""
        journaling_manager.recordScope("RedmineManager.log_learning", title=title, category=category)
        try:
            issue = self.redmine.issue.create(
                project_id=self.project_id,
                subject=title,
                description=description,
                tracker_id=1,  # 1 for learning
                category=category
            )
            journaling_manager.recordDebug(f"Logged learning event: {title}")
            return issue
            
        except Exception as e:
            journaling_manager.recordError(f"Error logging learning event: {e}")
            raise

    def log_training_result(self, model_name: str, accuracy: float, notes: str) -> Any:
        """Log training results"""
        journaling_manager.recordScope("RedmineManager.log_training_result", model_name=model_name, accuracy=accuracy)
        try:
            issue = self.redmine.issue.create(
                project_id=self.project_id,
                subject=f"Training Results: {model_name}",
                description=f"Accuracy: {accuracy}\nNotes: {notes}",
                tracker_id=2  # 2 for training
            )
            journaling_manager.recordDebug(f"Logged training results for {model_name}: {accuracy}")
            return issue
            
        except Exception as e:
            journaling_manager.recordError(f"Error logging training results: {e}")
            raise

    def get_learning_history(self, category: Optional[str] = None) -> Any:
        """Retrieve learning history"""
        journaling_manager.recordScope("RedmineManager.get_learning_history", category=category)
        try:
            filters = {'project_id': self.project_id}
            if category:
                filters['category'] = category
            history = self.redmine.issue.filter(**filters)
            journaling_manager.recordDebug(f"Retrieved learning history for category: {category}")
            return history
            
        except Exception as e:
            journaling_manager.recordError(f"Error retrieving learning history: {e}")
            raise 