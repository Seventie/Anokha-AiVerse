# backend/app/services/kroki_service.py

import httpx
import base64
import zlib
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class KrokiService:
    """
    Service for generating diagrams using Kroki API
    Kroki supports: PlantUML, Mermaid, GraphViz, etc.
    """
    
    def __init__(self, kroki_url: str = "https://kroki.io"):
        self.kroki_url = kroki_url
        self.timeout = 30.0
    
    def _encode_diagram(self, diagram_text: str) -> str:
        """Encode diagram text for Kroki URL"""
        compressed = zlib.compress(diagram_text.encode('utf-8'), 9)
        return base64.urlsafe_b64encode(compressed).decode('utf-8')
    
    async def generate_roadmap_diagram(
        self,
        roadmap_data: Dict,
        diagram_type: str = "mermaid"
    ) -> Dict[str, str]:
        """
        Generate visual roadmap diagram
        
        Args:
            roadmap_data: Structured roadmap with phases, skills, resources
            diagram_type: "mermaid" or "plantuml"
        
        Returns:
            Dict with diagram URLs (SVG, PNG)
        """
        try:
            if diagram_type == "mermaid":
                diagram_text = self._generate_mermaid_roadmap(roadmap_data)
            else:
                diagram_text = self._generate_plantuml_roadmap(roadmap_data)
            
            # Generate URLs
            encoded = self._encode_diagram(diagram_text)
            
            return {
                "svg_url": f"{self.kroki_url}/{diagram_type}/svg/{encoded}",
                "png_url": f"{self.kroki_url}/{diagram_type}/png/{encoded}",
                "diagram_text": diagram_text,
                "diagram_type": diagram_type
            }
        
        except Exception as e:
            logger.error(f"Failed to generate diagram: {e}")
            return {"error": str(e)}
    
    def _generate_mermaid_roadmap(self, roadmap_data: Dict) -> str:
        """Generate Mermaid flowchart for roadmap"""
        
        phases = roadmap_data.get("phases", [])
        current_skills = roadmap_data.get("current_skills", [])
        target_role = roadmap_data.get("target_role", "Target Role")
        
        # Start Mermaid diagram
        lines = ["graph TD"]
        lines.append(f'    START["🎯 Goal: {target_role}"]')
        
        # Current skills
        if current_skills:
            lines.append('    CURRENT["✅ Current Skills"]')
            lines.append('    START --> CURRENT')
            for i, skill in enumerate(current_skills[:5]):  # Limit to 5
                lines.append(f'    CS{i}["{skill}"]')
                lines.append(f'    CURRENT --> CS{i}')
        
        # Phases
        prev_node = "START" if not current_skills else "CURRENT"
        
        for phase_idx, phase in enumerate(phases):
            phase_num = phase_idx + 1
            phase_name = phase.get("phase_name", f"Phase {phase_num}")
            skills = phase.get("skills_to_learn", [])
            duration = phase.get("duration_weeks", 4)
            
            # Phase node
            phase_id = f"P{phase_num}"
            lines.append(f'    {phase_id}["📚 {phase_name}<br/>{duration} weeks"]')
            lines.append(f'    {prev_node} --> {phase_id}')
            
            # Skills in this phase
            for skill_idx, skill in enumerate(skills[:3]):  # Limit 3 per phase
                skill_id = f"P{phase_num}S{skill_idx}"
                skill_name = skill if isinstance(skill, str) else skill.get("name", "Skill")
                lines.append(f'    {skill_id}["{skill_name}"]')
                lines.append(f'    {phase_id} --> {skill_id}')
            
            prev_node = phase_id
        
        # End goal
        lines.append('    END["🎉 Ready for Role!"]')
        lines.append(f'    {prev_node} --> END')
        
        # Styling
        lines.append('    classDef startNode fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff')
        lines.append('    classDef phaseNode fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff')
        lines.append('    classDef skillNode fill:#FFC107,stroke:#333,stroke-width:1px')
        lines.append('    classDef endNode fill:#9C27B0,stroke:#333,stroke-width:2px,color:#fff')
        lines.append('    class START startNode')
        lines.append('    class END endNode')
        
        for i in range(len(phases)):
            lines.append(f'    class P{i+1} phaseNode')
        
        return "\n".join(lines)
    
    def _generate_plantuml_roadmap(self, roadmap_data: Dict) -> str:
        """Generate PlantUML diagram for roadmap"""
        
        phases = roadmap_data.get("phases", [])
        target_role = roadmap_data.get("target_role", "Target Role")
        
        lines = ["@startuml"]
        lines.append("skinparam rectangle {")
        lines.append("  BackgroundColor<<phase>> LightBlue")
        lines.append("  BackgroundColor<<skill>> LightYellow")
        lines.append("}")
        lines.append("")
        lines.append(f'rectangle "Goal: {target_role}" as START')
        
        prev = "START"
        for phase_idx, phase in enumerate(phases):
            phase_name = phase.get("phase_name", f"Phase {phase_idx + 1}")
            skills = phase.get("skills_to_learn", [])
            
            phase_id = f"Phase{phase_idx + 1}"
            lines.append(f'rectangle "{phase_name}" <<phase>> as {phase_id}')
            lines.append(f'{prev} --> {phase_id}')
            
            for skill_idx, skill in enumerate(skills[:3]):
                skill_name = skill if isinstance(skill, str) else skill.get("name", "Skill")
                skill_id = f"Skill{phase_idx}_{skill_idx}"
                lines.append(f'rectangle "{skill_name}" <<skill>> as {skill_id}')
                lines.append(f'{phase_id} --> {skill_id}')
            
            prev = phase_id
        
        lines.append(f'rectangle "Ready!" as END')
        lines.append(f'{prev} --> END')
        lines.append("@enduml")
        
        return "\n".join(lines)
    
    async def generate_skill_graph(
        self,
        skills: List[str],
        relationships: List[Dict[str, str]]
    ) -> Dict[str, str]:
        """
        Generate skill dependency graph
        
        Args:
            skills: List of skill names
            relationships: List of {"from": "skill1", "to": "skill2", "type": "prerequisite"}
        """
        try:
            # Generate Mermaid graph
            lines = ["graph LR"]
            
            for skill in skills:
                skill_id = skill.replace(" ", "_")
                lines.append(f'    {skill_id}["{skill}"]')
            
            for rel in relationships:
                from_id = rel["from"].replace(" ", "_")
                to_id = rel["to"].replace(" ", "_")
                rel_type = rel.get("type", "prerequisite")
                
                if rel_type == "prerequisite":
                    lines.append(f'    {from_id} -.->|prerequisite| {to_id}')
                elif rel_type == "related":
                    lines.append(f'    {from_id} ---|related| {to_id}')
                else:
                    lines.append(f'    {from_id} --> {to_id}')
            
            diagram_text = "\n".join(lines)
            encoded = self._encode_diagram(diagram_text)
            
            return {
                "svg_url": f"{self.kroki_url}/mermaid/svg/{encoded}",
                "png_url": f"{self.kroki_url}/mermaid/png/{encoded}",
                "diagram_text": diagram_text
            }
        
        except Exception as e:
            logger.error(f"Failed to generate skill graph: {e}")
            return {"error": str(e)}


# Singleton
kroki_service = KrokiService()
