from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Set
import logging
import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from collections import defaultdict
import json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import requests
import traceback
import google.generativeai as genai

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

app = FastAPI(
    title="Intelligent AI Traveling Agent",
    description="Self-learning travel assistant with dynamic knowledge expansion",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Embeddings model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Qdrant setup
try:
    qdrant_client = QdrantClient(
        url="http://localhost:6333"   # Local Docker
    )
    logger.info("✅ Qdrant client connected")

    COLLECTION_NAME = "travel_knowledge"

    if not qdrant_client.collection_exists(COLLECTION_NAME):
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        logger.info(f"✅ Collection '{COLLECTION_NAME}' created")
    else:
        logger.info(f"ℹ️ Collection '{COLLECTION_NAME}' already exists")

except Exception as e:
    logger.error(f"❌ Failed to connect Qdrant: {e}")
    qdrant_client = None

# ----------------------------
# Data ingestion
def ingest_travel_data(travel_docs: List[str], place: str = None):
    """Enhanced ingestion with place tracking"""
    try:
        vectors = embedder.encode(travel_docs).tolist()

        if not qdrant_client.collection_exists(COLLECTION_NAME):
            qdrant_client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE)
            )

        points = []
        for i, vector in enumerate(vectors):
            payload = {
                "doc": travel_docs[i],
                "timestamp": datetime.now().isoformat(),
                "place": place or "general",
                "source": "dynamic_learning" if place else "initial_data"
            }
            points.append(PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload))
        
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)

        # Update TF-IDF store
        if hasattr(app.state, 'vector_store'):
            existing_docs = app.state.vector_store["docs"]
            all_docs = existing_docs + travel_docs
        else:
            all_docs = travel_docs
            
        tfidf = TfidfVectorizer().fit(all_docs)
        tfidf_matrix = tfidf.transform(all_docs)
        
        app.state.vector_store = {
            "tfidf": tfidf, 
            "tfidf_matrix": tfidf_matrix, 
            "docs": all_docs
        }
        
        if place:
            intel_system.mark_as_learned(place)
        
        logger.info(f"Successfully ingested {len(travel_docs)} documents" + 
                   (f" for {place}" if place else ""))
        return True
        
    except Exception as e:
        logger.error(f"Error in enhanced ingest: {e}")
        return False

# ----------------------------
# Intelligence System State
class IntelligenceSystem:
    def __init__(self):
        self.unknown_places = defaultdict(int)
        self.learning_queue = set()
        self.recently_learned = set()
        self.user_contributions = []
        self.last_cleanup = datetime.now()
        
    def track_unknown_place(self, place: str):
        self.unknown_places[place] += 1
        logger.info(f"Unknown place '{place}' requested {self.unknown_places[place]} times")
        if self.unknown_places[place] >= 2:
            self.learning_queue.add(place)
            logger.info(f"Added '{place}' to learning queue")
    
    def mark_as_learned(self, place: str):
        if place in self.learning_queue:
            self.learning_queue.remove(place)
        self.recently_learned.add(place)
        if place in self.unknown_places:
            del self.unknown_places[place]
    
    def cleanup_old_data(self):
        if datetime.now() - self.last_cleanup > timedelta(hours=24):
            self.unknown_places.clear()
            self.recently_learned.clear()
            self.last_cleanup = datetime.now()

intel_system = IntelligenceSystem()

# ----------------------------
# Pydantic Models
class QA(BaseModel):
    question: str
    answer: str

class QuestionInput(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    question: str
    answer: str
    data_sources: List[str]
    learned_new_info: bool
    history: List[QA]
    confidence_level: Optional[str] = None

class ContributeInfo(BaseModel):
    place: str
    information: str
    user_id: Optional[str] = "anonymous"

# ----------------------------
# Enhanced Knowledge Management
def extract_place_names(text: str) -> List[str]:
    import re
    place_indicators = ['in ', 'to ', 'from ', 'visit ', 'about ', 'around ']
    places = []
    for indicator in place_indicators:
        pattern = fr'{indicator}([A-Z][a-zA-Z\s]+?)(?:\s|$|,|\.|!|\?)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        places.extend([match.strip() for match in matches])
    capitalized = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
    places.extend(capitalized)
    return list(set(places))

async def search_web_for_place(place: str) -> List[str]:
    try:
        mock_results = [
            f"{place} is a popular destination known for its unique attractions and cultural heritage.",
            f"Travelers to {place} often recommend visiting during the best season for optimal weather.",
            f"The local cuisine in {place} features traditional dishes that reflect the regional culture.",
            f"Popular activities in {place} include sightseeing, cultural experiences, and outdoor adventures.",
            f"Transportation in {place} is accessible through various local and international connections."
        ]
        logger.info(f"Found web information for {place}")
        return mock_results
    except Exception as e:
        logger.error(f"Web search failed for {place}: {e}")
        return []

# ----------------------------
# Intelligent Retrieval
def retrieve_with_intelligence(query: str, store: dict, docs: List[str], top_k=5) -> tuple[List[str], str, List[str]]:
    try:
        query_vec = embedder.encode([query])[0]
        results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vec,
            limit=top_k * 2,
            with_payload=True,
            score_threshold=0.3
        )
        sem_docs, sources, scores = [], [], []
        for r in results:
            sem_docs.append(r.payload["doc"])
            sources.append(r.payload.get("source", "unknown"))
            scores.append(r.score)
        if "tfidf" in store:
            query_tfidf = store["tfidf"].transform([query])
            sim_scores = cosine_similarity(query_tfidf, store["tfidf_matrix"]).flatten()
            top_idx = sim_scores.argsort()[::-1][:top_k]
            keyword_docs = [docs[i] for i in top_idx if i < len(docs) and sim_scores[i] > 0.1]
        else:
            keyword_docs = []
        all_docs = sem_docs + keyword_docs
        unique_docs = list(dict.fromkeys(all_docs))[:top_k]
        avg_score = sum(scores[:3]) / min(3, len(scores)) if scores else 0
        if avg_score > 0.7:
            confidence = "high"
        elif avg_score > 0.4:
            confidence = "medium"
        elif avg_score > 0:
            confidence = "low"
        else:
            confidence = "very_low"
        return unique_docs, confidence, list(set(sources))
    except Exception as e:
        logger.error(f"Intelligent retrieval failed: {e}")
        return [], "error", ["fallback"]

# ----------------------------
# Smart Prompt Engineering
def create_intelligent_prompt(question: str, context_docs: List[str], places: List[str]) -> str:
    context = "\n---\n".join(context_docs) if context_docs else "No specific information available."
    unknown_places_text = ", ".join(places) if places else "the requested location"
    prompt = f"Limited info on {unknown_places_text}.\nContext:\n{context}\nQuestion: {question}\nProvide practical travel advice while being honest about information gaps."
    return prompt

# ----------------------------
# Gemini Integration
def generate_intelligent_answer(question: str, context_docs: List[str], places: List[str]) -> str:
    prompt = create_intelligent_prompt(question, context_docs, places)
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # This is the corrected structure for the content
        response = model.generate_content([
            {"role": "user", "parts": [{"text": prompt}]}
        ])
        
        return response.text.strip() if response and response.text else "Sorry, I couldn't generate a response."
    except Exception as e:
        logger.error(f"Gemini request failed: {e}")
        return "I'm currently unable to process your request. Please try again later or consult reliable travel resources."
# ----------------------------
# Background Learning Tasks
async def background_learner():
    while True:
        try:
            intel_system.cleanup_old_data()
            if intel_system.learning_queue:
                place = intel_system.learning_queue.pop()
                logger.info(f"Learning about {place}...")
                new_info = await search_web_for_place(place)
                if new_info:
                    ingest_travel_data(new_info, place)
                    logger.info(f"Successfully learned about {place}")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Background learning error: {e}")
            await asyncio.sleep(300)

# ----------------------------
# API Endpoints
@app.on_event("startup")
async def startup_tasks():
    travel_knowledge = [
        "Paris, France is famous for the Eiffel Tower, Louvre Museum, Seine River cruises, and charming café culture.",
        "Tokyo, Japan offers diverse attractions including Shibuya Crossing, Tokyo Tower, ancient temples, and modern technology districts.",
        "New York City features iconic landmarks like Times Square, Central Park, Statue of Liberty, and world-class Broadway shows.",
        "The Maldives is renowned for luxury overwater resorts, crystal-clear waters perfect for snorkeling and diving, and pristine white sandy beaches.",
        "Dubai, UAE showcases the Burj Khalifa, thrilling desert safaris, luxury shopping malls, and innovative architecture.",
        "Rome, Italy captivates visitors with the Colosseum, Vatican City, ancient Roman Forum, and authentic Italian cuisine.",
        "Bali, Indonesia is known for beautiful temples, terraced rice fields, volcanic landscapes, and wellness retreats.",
        "London, England offers Big Ben, British Museum, Tower Bridge, and rich royal history with modern cultural scenes.",
        "Thailand combines bustling Bangkok markets, serene temples, tropical beaches in Phuket, and delicious street food.",
        "Iceland provides stunning natural wonders including Northern Lights, geysers, waterfalls, and unique volcanic landscapes."
    ]
    success = ingest_travel_data(travel_knowledge)
    if success:
        logger.info("Successfully loaded initial travel knowledge base")
    else:
        logger.error("Failed to load initial knowledge base")
    asyncio.create_task(background_learner())
    logger.info("Started background learning system")

@app.post("/ask", response_model=AnswerResponse)
async def intelligent_ask(request: Request, input: QuestionInput):
    try:
        places = extract_place_names(input.question)
        store = getattr(app.state, 'vector_store', {"docs": []})
        docs = store.get("docs", [])
        relevant_docs, confidence, sources = retrieve_with_intelligence(input.question, store, docs)
        learned_new_info = False
        if confidence in ["low", "very_low"] and places:
            for place in places:
                intel_system.track_unknown_place(place)
                if intel_system.unknown_places[place] >= 3:
                    new_info = await search_web_for_place(place)
                    if new_info:
                        ingest_travel_data(new_info, place)
                        relevant_docs, confidence, sources = retrieve_with_intelligence(input.question, store, docs)
                        learned_new_info = True
        answer = generate_intelligent_answer(input.question, relevant_docs, places)
        confidence_map = {
            "high": "High - Based on comprehensive information",
            "medium": "Medium - Based on available information", 
            "low": "Low - Limited specific information available",
            "very_low": "Very Low - General guidance provided",
            "error": "Error - Technical difficulties encountered"
        }
        return AnswerResponse(
            question=input.question,
            answer=answer,
            confidence_level=confidence_map.get(confidence, "Unknown"),
            data_sources=sources,
            learned_new_info=learned_new_info,
            history=[QA(question=input.question, answer=answer)]
        )
    except Exception as e:
        logger.error(f"Intelligent ask failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Processing failed - please try again")

@app.post("/contribute")
async def contribute_knowledge(contribution: ContributeInfo):
    try:
        if len(contribution.information.strip()) < 10:
            raise HTTPException(status_code=400, detail="Information too short")
        intel_system.user_contributions.append({
            "place": contribution.place,
            "info": contribution.information,
            "user_id": contribution.user_id,
            "timestamp": datetime.now().isoformat()
        })
        ingest_travel_data([contribution.information], contribution.place)
        logger.info(f"New contribution for {contribution.place} from {contribution.user_id}")
        return {
            "status": "success",
            "message": f"Thank you for contributing information about {contribution.place}!"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contribution failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process contribution")

@app.get("/system-status")
async def get_system_status():
    return {
        "status": "operational",
        "unknown_places_being_tracked": len(intel_system.unknown_places),
        "learning_queue_size": len(intel_system.learning_queue),
        "recently_learned_places": len(intel_system.recently_learned),
        "total_contributions": len(intel_system.user_contributions),
        "last_cleanup": intel_system.last_cleanup.isoformat(),
        "most_requested_unknown": dict(intel_system.unknown_places) if intel_system.unknown_places else {}
    }

@app.get("/health")
def health_check():
    return {
        "status": "Intelligent AI Travel Agent operational",
        "version": "3.0.0",
        "features": [
            "Self-learning system",
            "Dynamic knowledge expansion", 
            "Confidence-based responses",
            "User contributions",
            "Background research"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
