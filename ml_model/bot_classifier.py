import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib

class BotClassifier:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.scaler = StandardScaler()
        self.feature_names = [
            'timeOnPage', 'totalMouseMovements', 'totalClicks', 'totalScrollEvents',
            'avgMouseSpeed', 'mouseSpeedVariance', 'avgTimeBetweenMoves', 
            'straightLineRatio', 'avgClickInterval', 'clickIntervalVariance',
            'avgScrollSpeed', 'scrollDirection', 'doubleClickCount'
        ]

    def generate_synthetic_data(self, n_samples=10000):
        """Generate synthetic training data for human vs bot behavior"""
        np.random.seed(42)
        
        # Human behavior patterns
        human_data = []
        for _ in range(n_samples // 2):
            human_data.append([
                np.random.normal(45, 20),      # timeOnPage (30-60s typical)
                np.random.normal(150, 50),     # totalMouseMovements (varied)
                np.random.normal(8, 4),        # totalClicks (moderate)
                np.random.normal(12, 6),       # totalScrollEvents
                np.random.normal(200, 100),    # avgMouseSpeed (natural)
                np.random.normal(5000, 2000),  # mouseSpeedVariance (high variance)
                np.random.normal(100, 50),     # avgTimeBetweenMoves
                np.random.normal(0.3, 0.2),    # straightLineRatio (curved movements)
                np.random.normal(800, 400),    # avgClickInterval (varied)
                np.random.normal(50000, 20000), # clickIntervalVariance (high)
                np.random.normal(300, 150),    # avgScrollSpeed
                np.random.normal(0.1, 0.3),    # scrollDirection (mixed)
                np.random.poisson(1)           # doubleClickCount (occasional)
            ])
        
        # Bot behavior patterns
        bot_data = []
        for _ in range(n_samples // 2):
            bot_data.append([
                np.random.normal(15, 5),       # timeOnPage (shorter)
                np.random.normal(50, 20),      # totalMouseMovements (fewer)
                np.random.normal(15, 5),       # totalClicks (more systematic)
                np.random.normal(20, 5),       # totalScrollEvents (regular)
                np.random.normal(800, 200),    # avgMouseSpeed (faster, consistent)
                np.random.normal(1000, 500),   # mouseSpeedVariance (lower variance)
                np.random.normal(50, 10),      # avgTimeBetweenMoves (regular)
                np.random.normal(0.8, 0.1),    # straightLineRatio (straight lines)
                np.random.normal(200, 50),     # avgClickInterval (regular)
                np.random.normal(5000, 2000),  # clickIntervalVariance (lower)
                np.random.normal(600, 100),    # avgScrollSpeed (consistent)
                np.random.normal(0.8, 0.1),    # scrollDirection (mostly down)
                0                              # doubleClickCount (no double clicks)
            ])
        
        # Combine data
        X = np.array(human_data + bot_data)
        y = np.array([0] * (n_samples // 2) + [1] * (n_samples // 2))  # 0=human, 1=bot
        
        return X, y

    def train_model(self):
        """Train the bot detection model"""
        print("Generating synthetic training data...")
        X, y = self.generate_synthetic_data()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        print("Training Random Forest model...")
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        print(f"Training Accuracy: {train_score:.3f}")
        print(f"Testing Accuracy: {test_score:.3f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 5 Most Important Features:")
        print(feature_importance.head())
        
        # Create pipeline model that includes scaling
        import pickle
        
        class ScaledRandomForest:
            def __init__(self, scaler, model):
                self.scaler = scaler
                self.model = model
            
            def predict_proba(self, X):
                X_scaled = self.scaler.transform(X)
                return self.model.predict_proba(X_scaled)
            
            def predict(self, X):
                X_scaled = self.scaler.transform(X)
                return self.model.predict(X_scaled)
        
        return ScaledRandomForest(self.scaler, self.model)

    def save_model(self, filepath):
        """Save the trained model"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }, filepath)

    def load_model(self, filepath):
        """Load a trained model"""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']

if __name__ == "__main__":
    # Train and save model
    classifier = BotClassifier()
    trained_model = classifier.train_model()
    
    # Save model components separately to avoid pickling issues
    import os
    os.makedirs('../ml_model', exist_ok=True)
    
    # Save individual components
    joblib.dump({
        'scaler': trained_model.scaler,
        'model': trained_model.model,
        'feature_names': classifier.feature_names
    }, '../ml_model/bot_classifier.pkl')
    
    print("Model saved successfully!")