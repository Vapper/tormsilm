from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModel
import torch
import numpy as np
from typing import List, Dict, Union

class EstBERTProcessor:
    def __init__(self, task_type: str = 'classification'):
        # Initialize the base EstBERT tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained('tartuNLP/EstBERT')
        
        # Choose model type based on task
        if task_type == 'classification':
            self.model = AutoModelForSequenceClassification.from_pretrained(
                'tartuNLP/EstBERT',
                num_labels=3  # Adjust based on your classification needs
            )
        elif task_type == 'embedding':
            self.model = AutoModel.from_pretrained('tartuNLP/EstBERT')
        
        # Move model to GPU if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        
        # Maximum sequence length for EstBERT
        self.max_length = 512

    def preprocess_text(self, text: str) -> str:
        """
        Prepare Estonian text for BERT processing
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Handle Estonian-specific characters
        # EstBERT handles õ,ä,ö,ü naturally, but we should ensure proper encoding
        text = text.encode('utf-8').decode('utf-8')
        
        return text

    def encode_text(self, texts: Union[str, List[str]], padding: bool = True) -> Dict:
        """
        Encode text(s) using EstBERT tokenizer
        """
        # Handle single text input
        if isinstance(texts, str):
            texts = [texts]
            
        # Tokenize and encode
        encoded = self.tokenizer(
            texts,
            padding=padding,
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # Move to device
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        
        return encoded

    def get_embeddings(self, text: str) -> np.ndarray:
        """
        Get embeddings from EstBERT for semantic similarity tasks
        """
        # Preprocess and encode
        processed_text = self.preprocess_text(text)
        encoded = self.encode_text(processed_text)
        
        # Get BERT embeddings
        with torch.no_grad():
            outputs = self.model(**encoded)
            
        # Use [CLS] token embedding (first token)
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        
        return embeddings

    def classify_text(self, text: str) -> Dict[str, float]:
        """
        Classify text using EstBERT
        """
        # Preprocess and encode
        processed_text = self.preprocess_text(text)
        encoded = self.encode_text(processed_text)
        
        # Get classification predictions
        with torch.no_grad():
            outputs = self.model(**encoded)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # Convert to dictionary of label probabilities
        labels = ['impact_severe', 'impact_moderate', 'impact_minor']  # Adjust based on your needs
        predictions = {
            label: prob.item() 
            for label, prob in zip(labels, probabilities[0])
        }
        
        return predictions

    def semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two Estonian texts
        """
        # Get embeddings for both texts
        emb1 = self.get_embeddings(text1)
        emb2 = self.get_embeddings(text2)
        
        # Calculate cosine similarity
        similarity = np.dot(emb1, emb2.T) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )
        
        return similarity[0][0]

estbert = EstBERTProcessor()
estbert.classify_text("Esmaspäeva hommikuks vaibuvad Eestis tormituuled ja ka vihma jääb vähemaks, ent öised miinuskraadid muudavad teed kohati libedaks.")