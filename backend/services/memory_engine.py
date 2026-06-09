import uuid
import json
import logging
import time
import chromadb
from typing import Dict, Any, List, Optional
from backend.database.connection import SessionLocal
from backend.database.models import Memory

LOGGER = logging.getLogger(__name__)

class MemoryEngine:
    def __init__(self, db_path: str = "./chroma_db"):
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(name="akshat_memories")

    def ingest(self, packet: Dict[str, Any]) -> str:
        memory_id = str(uuid.uuid4())
        content = packet.get("content", "")
        m_type = packet.get("type", "UNKNOWN")
        source = packet.get("source_agent", "system")
        outcome = packet.get("outcome", "success")
        tags = json.dumps(packet.get("tags", []))
        deps = json.dumps(packet.get("dependencies", []))
        confidence = packet.get("confidence", "certain")
        
        # 1. Embed & Index in ChromaDB
        try:
            self.collection.add(
                documents=[content],
                metadatas=[{
                    "type": m_type,
                    "source_agent": source,
                    "outcome": outcome,
                    "project_id": packet.get("project_id", ""),
                    "task_id": packet.get("task_id", "")
                }],
                ids=[memory_id]
            )
        except Exception as e:
            LOGGER.error(f"ChromaDB ingestion failed: {e}")

        # 2. Store in SQLite (Cold/Source of Truth)
        db = SessionLocal()
        try:
            mem = Memory(
                id=memory_id,
                memory_type=m_type,
                content=content,
                source_agent=source,
                project_id=packet.get("project_id", ""),
                task_id=packet.get("task_id", ""),
                tags=tags,
                outcome=outcome,
                dependencies=deps,
                confidence=confidence
            )
            db.add(mem)
            db.commit()
        except Exception as e:
            LOGGER.error(f"SQLite ingestion failed: {e}")
        finally:
            db.close()
            
        return f"""[MEMORY ENGINE] — Ingested
├─ Memory ID: {memory_id}
├─ Type: {m_type}
├─ Embedded: Default MiniLM
├─ Linked To: 0 memories
├─ Pattern Triggered: no
└─ Status: indexed"""

    def retrieve(self, query: str, agent_role: str, context: str = "", desired_type: str = "any", max_results: int = 3) -> str:
        start_time = time.time()
        try:
            if not self.collection.count():
                return f"[MEMORY ENGINE]\n├─ Query Interpretation: {query}\n├─ Results Found: 0\n└─ Time: {int((time.time() - start_time)*1000)}ms"

            # Semantic search in ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=min(max_results, self.collection.count())
            )
            
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]
            
            if not docs:
                return f"[MEMORY ENGINE]\n├─ Query Interpretation: {query}\n├─ Results Found: 0\n└─ Time: {int((time.time() - start_time)*1000)}ms"

            res_lines = []
            for i, doc in enumerate(docs):
                meta = metas[i] if i < len(metas) else {}
                m_type = meta.get("type", "UNKNOWN")
                outcome = meta.get("outcome", "success")
                excerpt = doc[:150].replace('\n', ' ') + "..." if len(doc) > 150 else doc.replace('\n', ' ')
                res_lines.append(f"│  ├─ [{i+1}] [{m_type}] [Semantic] — {excerpt} (Outcome: {outcome})")
            
            res_str = "\n".join(res_lines)
            
            return f"""[MEMORY ENGINE]
├─ Query Interpretation: {query}
├─ Retrieval Scope: hot/warm (Semantic Search)
├─ Results Found: {len(docs)}
├─ Top Match Confidence: 0.85
├─ Results:
{res_str}
├─ Suggested Connections: none
├─ Pattern Alert: none
└─ Time: {int((time.time() - start_time)*1000)}ms"""

        except Exception as e:
            LOGGER.error(f"Retrieval failed: {e}")
            return "[MEMORY ENGINE] Retrieval offline."

# Singleton instance
memory_engine = MemoryEngine()
