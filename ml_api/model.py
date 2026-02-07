"""
Iris Classifier Model
=====================

This module contains a simple ML model for classifying iris flowers.

THE IRIS DATASET:
-----------------
Classic ML dataset from 1936. Contains measurements of 150 iris flowers:
- 4 features: sepal length, sepal width, petal length, petal width
- 3 classes: setosa, versicolor, virginica

WHY IRIS?
---------
- Simple enough to understand
- Complex enough to be interesting
- Built into scikit-learn (no data download needed)
- Perfect for learning ML + monitoring concepts

MODEL CHOICE:
-------------
We use RandomForestClassifier because:
- Works well out of the box (no hyperparameter tuning needed)
- Handles the iris dataset perfectly
- Fast inference (important for API latency)
"""

import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
from typing import Tuple, List

# Class names for the iris dataset
IRIS_CLASSES = ['setosa', 'versicolor', 'virginica']

# Path to save/load the trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'iris_model.joblib')


class IrisClassifier:
    """
    Wrapper around scikit-learn model for iris classification.

    Encapsulates:
    - Model training
    - Prediction
    - Model persistence (save/load)
    - Accuracy evaluation
    """

    def __init__(self):
        """Initialize the classifier."""
        self.model = None
        self.accuracy = 0.0
        self.is_trained = False

        # Store test data for ongoing evaluation
        self._X_test = None
        self._y_test = None

    def train(self) -> float:
        """
        Train the model on the iris dataset.

        Returns:
            float: Accuracy on the test set (0.0 to 1.0)

        TRAINING PROCESS:
        1. Load iris dataset (built into sklearn)
        2. Split into train (80%) and test (20%) sets
        3. Train RandomForest on training data
        4. Evaluate on test data
        5. Store test data for future evaluation
        """
        # Load the famous iris dataset
        # X = features (measurements), y = labels (species)
        iris = load_iris()
        X, y = iris.data, iris.target

        # Split data: 80% train, 20% test
        # random_state ensures reproducible splits
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42  # For reproducibility
        )

        # Store test data for evaluation
        self._X_test = X_test
        self._y_test = y_test

        # Create and train the model
        # n_estimators = number of trees in the forest
        # random_state = reproducibility
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )

        # fit() is where the actual learning happens
        self.model.fit(X_train, y_train)

        # Evaluate accuracy
        self.accuracy = self.evaluate()
        self.is_trained = True

        return self.accuracy

    def predict(self, features: List[float]) -> Tuple[str, List[float]]:
        """
        Make a prediction for given iris measurements.

        Args:
            features: [sepal_length, sepal_width, petal_length, petal_width]

        Returns:
            Tuple of (predicted_class_name, probability_for_each_class)

        Example:
            >>> model.predict([5.1, 3.5, 1.4, 0.2])
            ('setosa', [0.97, 0.02, 0.01])
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained! Call train() first.")

        # Reshape for sklearn (expects 2D array)
        X = np.array(features).reshape(1, -1)

        # Get prediction (class index)
        prediction_idx = self.model.predict(X)[0]

        # Get probabilities for each class
        probabilities = self.model.predict_proba(X)[0].tolist()

        # Convert index to class name
        predicted_class = IRIS_CLASSES[prediction_idx]

        return predicted_class, probabilities

    def evaluate(self) -> float:
        """
        Evaluate model accuracy on test set.

        Returns:
            float: Accuracy score (0.0 to 1.0)

        This is useful for:
        - Monitoring model performance over time
        - Detecting model degradation
        """
        if self._X_test is None or self._y_test is None:
            return 0.0

        predictions = self.model.predict(self._X_test)
        return accuracy_score(self._y_test, predictions)

    def save(self, path: str = MODEL_PATH):
        """
        Save the trained model to disk.

        Uses joblib which is optimized for sklearn models.
        """
        if not self.is_trained:
            raise RuntimeError("Cannot save untrained model!")

        joblib.dump({
            'model': self.model,
            'accuracy': self.accuracy
        }, path)

    def load(self, path: str = MODEL_PATH) -> bool:
        """
        Load a pre-trained model from disk.

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not os.path.exists(path):
            return False

        data = joblib.load(path)
        self.model = data['model']
        self.accuracy = data['accuracy']
        self.is_trained = True
        return True


# =============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# =============================================================================

def get_model() -> IrisClassifier:
    """
    Get a trained model instance.

    Tries to load from disk first, trains new if not found.
    This is what the API will use.
    """
    model = IrisClassifier()

    # Try to load existing model
    if model.load():
        print(f"Loaded pre-trained model (accuracy: {model.accuracy:.2%})")
        return model

    # Train new model if not found
    print("Training new model...")
    accuracy = model.train()
    print(f"Model trained (accuracy: {accuracy:.2%})")

    # Save for next time
    model.save()
    print(f"Model saved to {MODEL_PATH}")

    return model
