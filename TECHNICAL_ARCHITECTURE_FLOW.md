# 🏗️ SmartBorrow Technical Architecture Flow

## 📊 2D System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Dashboard     │  │  Ask Question   │  │  Cost Calc      │              │
│  │   (Streamlit)   │  │   (Streamlit)   │  │  (Streamlit)    │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│           │                     │                     │                      │
│           └─────────────────────┼─────────────────────┘                      │
│                                 │                                            │
└─────────────────────────────────┼────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    Enhanced Coordinator Agent                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │   Query     │  │   Intent    │  │   Route     │  │   Combine   │ │   │
│  │  │ Analysis    │  │ Detection   │  │   Query     │  │  Responses  │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│           │                     │                     │                      │
│           ▼                     ▼                     ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   RAG       │  │   Web       │  │   Calc      │  │   Multi-    │      │
│  │  Pipeline   │  │   Search    │  │   Agent     │  │   Agent     │      │
│  │             │  │             │  │             │  │  Workflow   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘
           │                     │                     │                      │
           ▼                     ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SPECIALIZED AGENT LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Loan      │  │   Grant     │  │ Calculator  │  │ Researcher  │      │
│  │ Specialist  │  │ Specialist  │  │   Agent     │  │   Agent     │      │
│  │             │  │             │  │             │  │             │      │
│  │ • Interest  │  │ • Pell      │  │ • EFC       │  │ • Current   │      │
│  │   Rates     │  │   Grants    │  │   Calc      │  │   Rates     │      │
│  │ • Repayment │  │ • Eligibility│  │ • Cost      │  │ • Policy    │      │
│  │   Plans     │  │ • Amounts   │  │   Analysis  │  │   Updates   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘
           │                     │                     │                      │
           ▼                     ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DATA PROCESSING LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Vector    │  │   Web       │  │   Financial │  │   Real-time │      │
│  │   Store     │  │   Cache     │  │   Data      │  │   APIs      │      │
│  │  (FAISS)    │  │ (Tavily)    │  │  (Calculators)│  │ (Tavily)    │      │
│  │             │  │             │  │             │  │             │      │
│  │ • Federal   │  │ • Cached    │  │ • Interest  │  │ • Current   │      │
│  │   Aid Docs  │  │   Results   │  │   Rates     │  │   Policies  │      │
│  │ • Embeddings│  │ • TTL Cache │  │ • Formulas  │  │ • Deadlines │      │
│  │ • Metadata  │  │ • Hit Rate  │  │ • Rules     │  │ • Updates   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘
           │                     │                     │                      │
           ▼                     ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        EVALUATION LAYER                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   RAGAS     │  │   Quality   │  │ Performance │  │   User      │      │
│  │ Evaluation  │  │   Metrics   │  │ Monitoring  │  │   Feedback  │      │
│  │             │  │             │  │             │  │             │      │
│  │ • Faithful- │  │ • Accuracy  │  │ • Response  │  │ • Satisfaction│      │
│  │   ness      │  │ • Relevance │  │   Time      │  │ • Helpful-  │      │
│  │ • Relevance │  │ • Complete- │  │ • Through-  │  │   ness      │      │
│  │ • Precision │  │   ness      │  │   put       │  │ • Usability │      │
│  │ • Recall    │  │ • Clarity   │  │ • Error     │  │ • Impact    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Detailed Flow Explanation

### **1. User Input Flow**
```
User Question → UI Layer → Orchestration Layer → Specialized Agents → Data Processing → Evaluation → Response
```

### **2. Session Integration Points**

#### **Session 1-2 (Prompt Engineering)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  Specialized    │───▶│  Structured     │
│                 │    │   Prompts       │    │   Response      │
│ "How do I...?"  │    │ • Loan Expert   │    │ • Bullet Points │
│                 │    │ • Grant Expert  │    │ • Bold Text     │
│                 │    │ • Calc Expert   │    │ • Sources       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### **Session 3 (Basic RAG)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   Vector Store  │───▶│   Context       │
│                 │    │   (FAISS)       │    │   Retrieval     │
│ "Pell Grant?"   │    │ • Embeddings    │    │ • Relevant Docs │
│                 │    │ • Similarity    │    │ • Chunking      │
│                 │    │ • Search        │    │ • Ranking       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### **Session 4 (Production RAG)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LangChain     │───▶│   LangSmith     │───▶│   Quality       │
│   LCEL          │    │   Monitoring    │    │   Metrics       │
│ • Orchestration │    │ • Performance   │    │ • RAGAS         │
│ • Error Handling│    │ • Debugging     │    │ • Evaluation    │
│ • Fallbacks     │    │ • Tracing       │    │ • Improvement   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### **Session 5-6 (Multi-Agent)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Coordinator   │───▶│   Specialized   │───▶│   Combined      │
│   Agent         │    │   Agents        │    │   Response      │
│ • Query Routing │    │ • Loan Specialist│    │ • Multi-source  │
│ • Intent Detect │    │ • Grant Specialist│   │ • Coordinated   │
│ • Tool Select   │    │ • Calculator    │    │ • Structured    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### **Session 7-8 (Synthetic Data + RAGAS)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Synthetic     │───▶│   RAGAS         │───▶│   Quality       │
│   Data Gen      │    │   Evaluation    │    │   Assurance     │
│ • Q&A Pairs     │    │ • Faithfulness  │    │ • Metrics       │
│ • Test Cases    │    │ • Relevance     │    │ • Monitoring    │
│ • Coverage      │    │ • Precision     │    │ • Improvement   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### **Session 9-10 (Advanced Retrieval + Agents)**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Advanced      │───▶│   Intelligent   │───▶│   Enhanced      │
│   Retrieval     │    │   Routing       │    │   Responses     │
│ • Hybrid Search │    │ • Tool Selection│    │ • Better Quality│
│ • Multi-Query   │    │ • Reasoning     │    │ • Faster Speed  │
│ • Ensemble      │    │ • Fallbacks     │    │ • Higher Acc    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Data Flow Through Sessions

### **Complete User Journey Example:**

```
1. User: "How do I qualify for a Pell Grant?"
   │
   ▼ Session 3 (Basic RAG)
2. Query → Embeddings → Vector Search → Context Retrieval
   │
   ▼ Session 9 (Advanced Retrieval)  
3. Multi-Query: "Pell Grant" → "federal aid" + "financial need" + "EFC"
   │
   ▼ Session 5-6 (Multi-Agent)
4. Coordinator → Route to Grant Specialist Agent
   │
   ▼ Session 1-2 (Prompt Engineering)
5. Grant Specialist → Specialized Pell Grant prompt
   │
   ▼ Session 10 (Advanced Agents)
6. Agent → Choose tools: Eligibility calculator + Web search
   │
   ▼ Session 4 (Production RAG)
7. LangChain LCEL → Orchestrate response generation
   │
   ▼ Session 7-8 (Evaluation)
8. RAGAS → Evaluate faithfulness, relevance, precision
   │
   ▼ Session 4 (Production)
9. LangSmith → Monitor performance and quality
   │
   ▼ UI Layer
10. Streamlit → Display structured response with sources
```

## 🔧 Technical Integration Matrix

| Session | Input | Processing | Output | Next Session |
|---------|-------|------------|--------|--------------|
| 1-2 | User Query | Specialized Prompts | Structured Response | 3 |
| 3 | Query | Vector Search | Context | 4 |
| 4 | Context | LangChain LCEL | Orchestrated Response | 5-6 |
| 5-6 | Response | Agent Coordination | Multi-Agent Response | 7-8 |
| 7-8 | Response | RAGAS Evaluation | Quality Metrics | 9-10 |
| 9-10 | Metrics | Advanced Retrieval | Enhanced Response | UI |

## 🚀 Performance Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Input         │───▶│   Processing    │───▶│   Output        │
│   (2.46s)       │    │   (Multi-layer) │    │   (Structured)  │
│                 │    │                 │    │                 │
│ • User Query    │    │ • RAG Pipeline  │    │ • Bullet Points │
│ • Intent Detect │    │ • Agent Routing │    │ • Bold Text     │
│ • Context Prep  │    │ • Tool Selection│    │ • Sources       │
│ • Query Expand  │    │ • Response Gen  │    │ • Confidence    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

*This technical architecture shows how each session's learning flows through the system, creating a production-ready AI application that delivers real value to users.* 