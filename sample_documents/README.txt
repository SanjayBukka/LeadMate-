SAMPLE DOCUMENTS FOR LEAD MATE APPLICATION
==========================================

This folder contains sample documents for testing the Lead Mate platform features.

CONTENTS:
---------

1. PROJECT DOCUMENTATION
   - Project_Requirements.txt
     Complete project requirements document for an E-Commerce Platform
     Use this to test: Document upload in Manager Dashboard
   
   - Technical_Specifications.md
     Technical specifications with database schemas, API endpoints, and architecture
     Use this to test: Document analysis with DocAgent

2. CANDIDATE RESUMES (5 files)
   All resumes are for testing the Team Formation Agent feature:

   - Resume_Sarah_Johnson.txt
     Senior Frontend Developer (React, TypeScript expert)
     6 years experience, perfect for frontend lead role
   
   - Resume_Michael_Chen.txt
     Backend Developer (Node.js, MongoDB specialist)
     5 years experience, strong in API development
   
   - Resume_Emily_Rodriguez.txt
     Full-Stack Developer (React + Node.js)
     4 years experience, versatile developer
   
   - Resume_David_Kumar.txt
     DevOps Engineer (AWS, Docker, Kubernetes expert)
     5 years experience, infrastructure specialist
   
   - Resume_Jessica_Williams.txt
     UI/UX Designer & Frontend Developer
     4 years experience, design + development skills

HOW TO USE:
-----------

STEP 1: Upload Project Documents
1. Login as Manager
2. Create a new project
3. Upload "Project_Requirements.txt" and "Technical_Specifications.md"
4. These will be analyzed and stored in the vector database

STEP 2: Test DocAgent
1. Switch to Team Lead view
2. Go to Agents Hub > DocAgent
3. Ask questions about the uploaded documents:
   - "What are the main features of this project?"
   - "What technology stack is required?"
   - "How many developers do we need?"
   - "What are the technical requirements?"

STEP 3: Test StackAgent
1. Go to Agents Hub > StackAgent
2. Get technology stack recommendations based on project docs
3. The agent will analyze requirements and suggest appropriate tech stack

STEP 4: Test Team Formation Agent
1. Go to Agents Hub > TeamAgent
2. Upload all 5 resume files
3. The agent will match candidates to project requirements
4. You'll get recommendations for team composition:
   - Best fit candidates
   - Role assignments
   - Skill coverage analysis

STEP 5: Test Task Designer Agent
1. Go to Agents Hub > TaskAgent
2. Generate task breakdown based on project requirements
3. Get timeline estimates and task dependencies

EXPECTED RESULTS:
-----------------

✓ Documents should be successfully uploaded and processed
✓ DocAgent should answer questions accurately based on document content
✓ StackAgent should recommend: React, Node.js, MongoDB, AWS
✓ TeamAgent should recommend:
   - Sarah Johnson for Frontend Lead
   - Michael Chen for Backend Development
   - Emily Rodriguez for Full-Stack Development
   - David Kumar for DevOps
   - Jessica Williams for UI/UX Design
✓ TaskAgent should break down the project into phases and tasks

TIPS:
-----
- Make sure backend and frontend are running
- Ensure Ollama is running with llama3.2:3b model
- Check that MongoDB is connected
- Allow time for document processing (vector embeddings)

TROUBLESHOOTING:
----------------
- If upload fails: Check file permissions and backend logs
- If agent responses are slow: This is normal for local LLM (Ollama)
- If no recommendations: Ensure documents were fully processed
- If errors occur: Check backend terminal for detailed error messages

FOLDER LOCATION:
----------------
Desktop/Lead Mate full Application/sample_documents/

Last Updated: February 11, 2026
