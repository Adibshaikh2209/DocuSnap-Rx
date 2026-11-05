import os
import gradio as gr
from PIL import Image
from google import genai
from google.genai import types

# Fetch API key securely from system environment variables
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is missing. Set it before running.")

client = genai.Client(api_key=api_key)

# Official Gemma 4 Multimodal endpoint for Hacktoberfest
GEMMA_MODEL = "gemma-4-26b-a4b-it"

# Clinical & Document Auditor System Instruction
SYSTEM_PROMPT = """You are DocuSnap-Rx, an open-weights multimodal clinical and document auditor powered by Gemma 4. Analyze the uploaded image (handwritten doctor prescription, clinical lab report, medical bill, or study notes). Format your response strictly as:

### 1. Document Classification & Summary
State the document type (e.g., Handwritten Prescription, Lab Pathology Report, Pharmacy Invoice) in 1-2 concise lines.

### 2. Extracted Entities & Dosages/Totals
Transcribe handwritten/printed medicine names, dosages, frequencies, or billed line items clearly.

### 3. Automated Clinical & Discrepancy Audit
Verify mathematical totals or identify potential abnormal lab values / dosage ambiguities. Explicitly flag any illegible or blurry handwriting that requires human clarification.

### 4. Immediate Action Checklist
2 concrete, prioritized next steps for the patient or reviewing clinician.
"""


def audit_document(image: Image.Image, user_notes: str):
    if image is None:
        return "⚠️ Please upload or snap a photo of a document first."

    full_prompt = SYSTEM_PROMPT
    if user_notes.strip():
        full_prompt += f"\n\nUser Context / Specific Question:\n{user_notes}"

    try:
        try:
            # Gemma 4 primary endpoint
            response = client.models.generate_content(
                model=GEMMA_MODEL, contents=[image.convert("RGB"), full_prompt]
            )
        except Exception:
            # Reliable fallback in case of rate limits
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image.convert("RGB"), full_prompt],
            )
        return response.text
    except Exception as e:
        return f"Audit Error: {str(e)}"


# Gradio Interface
with gr.Blocks(theme=gr.themes.Soft(), title="DocuSnap-Rx") as demo:
    gr.Markdown("# 📷 DocuSnap-Rx: Multimodal Clinical & Document Auditor")
    gr.Markdown(
        "*Built with **Gemma 4** (`gemma-4-26b-a4b-it`) via Gemini API for Hacktoberfest.*  \n"
        "Upload a handwritten prescription, clinical lab sheet, or invoice to transcribe data and audit accuracy instantly."
    )

    with gr.Row():
        img_input = gr.Image(
            type="pil",
            label="Upload Document Photo (Prescription / Lab / Note)",
        )
        notes_input = gr.Textbox(
            label="Optional Note or Focus Query",
            placeholder="e.g., Verify the total price, or check the dosage of tablet #1",
            lines=2,
        )

    audit_btn = gr.Button("🔍 Audit Document with Gemma 4", variant="primary")
    output_display = gr.Markdown()

    audit_btn.click(
        fn=audit_document,
        inputs=[img_input, notes_input],
        outputs=output_display,
    )

if __name__ == "__main__":
    demo.launch(share=True)