#!/usr/bin/env python3
"""
Script to update agent models from gemini-1.5-pro to gemini-2.5-pro.
Run this from the backend directory: python update_agent_models.py
"""

import sys
from pathlib import Path

# Add the backend directory to the path so we can import app modules
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.agent import Agent
from app.core.database import SessionLocal


def update_agent_models():
    """Update all agents with gemini-1.5-pro to gemini-2.5-pro."""
    db = SessionLocal()
    
    try:
        # Find agents with the old model
        agents_to_update = db.query(Agent).filter(Agent.model == "gemini-1.5-pro").all()
        
        if not agents_to_update:
            print("No agents found with model 'gemini-1.5-pro'. Nothing to update.")
            return
        
        print(f"Found {len(agents_to_update)} agent(s) with model 'gemini-1.5-pro':")
        for agent in agents_to_update:
            print(f"  - {agent.name} (ID: {agent.id})")
        
        # Update all matching agents
        updated_count = db.query(Agent).filter(Agent.model == "gemini-1.5-pro").update(
            {Agent.model: "gemini-2.5-pro"}, 
            synchronize_session=False
        )
        
        db.commit()
        print(f"\n[SUCCESS] Successfully updated {updated_count} agent(s) to 'gemini-2.5-pro'")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error updating agents: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Updating agent models from gemini-1.5-pro to gemini-2.5-pro...")
    print("-" * 60)
    update_agent_models()
    print("-" * 60)
    print("Done!")

