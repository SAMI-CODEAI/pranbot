# Gemma 2 9B: Model Justification & Details

This document details the selection, architecture, and capabilities of the **Gemma 2 9B** Large Language Model (LLM) used in the Pran-Bot reporting system.

## 1. Why Gemma 2 9B?

The **Gemma 2 9B** model was selected as the intelligence engine for Pran-Bot after evaluating several candidates (Llama 3 8B, Mistral 7B, Phi-3). It represents the optimal balance for a locally-hosted industrial IoT application.

### 1.1 Key Selection Criteria

*   **Superior Reasoning at Scale:** Gemma 2 9B significantly outperforms other models in the <10B parameter class (and even some larger models) on reasoning benchmarks (MMLU, MATH, coding). This is critical for interpreting complex sensor correlations (e.g., distinguishing between a fire vs. simply high heat and humidity).
*   **Local Inference Capability:** 
    *   **Privacy:** Sensor data never leaves the local network. It is processed entirely on the `report_server`.
    *   **Reliability:** Works without an internet connection, essential for industrial environments where Pran-Bot might operate.
    *   **Cost:** Zero inference cost compared to paid APIs (OpenAI/Anthropic).
*   **Instruction Following:** The model excels at following strict formatting constraints (Markdown structure, specific headers, JSON outputs), which is necessary for generating the automated PDF reports.
*   **Hardware Efficiency:** With 9 billion parameters, it fits comfortably in the VRAM of most modern consumer availability GPUs (requiring ~6-8GB VRAM at 4-bit quantization), making the system accessible.

## 2. Model Architecture & Details

Gemma 2 is built on Google's Gemini research and architecture, adapted for open weights.

### 2.1 Technical Specifications

*   **Developer:** Google DeepMind
*   **Parameter Count:** ~9 Billion
*   **Context Window:** 8192 tokens (Sufficient for analyzing long history logs of sensor data).
*   **Architecture:** Decoder-only Transformer with significant modern optimizations.
    *   **Sliding Window Attention:** Alternates between local sliding window attention and global attention layers. This improves efficiency for long sequences without sacrificing long-term dependency modeling.
    *   **Logit Soft-Capping:** A technique that prevents logits from growing excessively large, stabilizing training and improving generation quality.
    *   **Knowledge Distillation:** The 9B model was trained by distilling knowledge from a much larger teacher model, resulting in "oversized" intelligence for its weight class.

### 2.2 Integration in Pran-Bot

The model is deployed using **Ollama**, an open-source runtime for LLMs.

1.  **Orchestration:** The Flask `report_server.py` constructs a prompt containing statistical summaries of the sensor data.
2.  **Inference:** The prompt is sent to the local Ollama instance running `gemma2:9b`.
3.  **Output:** The model generates a structured safety assessment, which is then parsed and rendered into the final PDF.

## 3. Performance vs. Alternatives

| Feature | Gemma 2 9B | Llama 3 8B | Mistral 7B |
| :--- | :--- | :--- | :--- |
| **Reasoning (MMLU)** | **High (~72%)** | High (~68%) | Moderate (~64%) |
| **Hallucination Rate** | **Low** | Low-Medium | Medium |
| **Instruction Following** | **Excellent** | Very Good | Good |
| **Safety Training** | **Robust** | Moderate | Minimal |

**Conclusion:** For a safety-critical application like Pran-Bot, the robust reasoning and safety tuning of Gemma 2 9B make it the superior choice.
