#!/usr/bin/env python
"""
Create a sample PDF file for testing SocioGraph.

This script creates a simple PDF file in the input directory
that can be used to test the ingestion pipeline.
"""

import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Sample text with entities and relationships
SAMPLE_TEXT = [
    "# The Global Climate Crisis",
    "",
    "The United Nations (UN) has identified climate change as the defining issue of our time. The Intergovernmental Panel on Climate Change (IPCC) was established by the UN to provide scientific assessments on climate change.",
    "",
    "According to the Paris Agreement, signed in 2015, countries committed to limit global warming to well below 2 degrees Celsius. The European Union has been a strong supporter of the Paris Agreement.",
    "",
    "The World Health Organization (WHO) has warned that climate change affects social and environmental determinants of health. WHO estimates that climate change will cause approximately 250,000 additional deaths per year between 2030 and 2050.",
    "",
    "Tesla, led by CEO Elon Musk, has been developing electric vehicles to reduce carbon emissions. Meanwhile, Microsoft, under the leadership of Satya Nadella, has pledged to be carbon negative by 2030.",
    "",
    "Scientists believe that the Amazon Rainforest, located primarily in Brazil, plays a crucial role in regulating the Earth's climate. Deforestation in the Amazon has increased carbon dioxide levels in the atmosphere.",
    "",    "The Green Climate Fund (GCF) was established to help developing countries adapt to climate change. The United States initially pledged $3 billion to the GCF but later withdrew support under President Donald Trump's administration.",
]

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.app.core.config import get_config


def create_sample_pdf():
    """Create a sample PDF file in the input directory."""
    config = get_config()
    
    # Ensure input directory exists
    config.INPUT_DIR.mkdir(exist_ok=True)
      # Create PDF file
    pdf_path = config.INPUT_DIR / "climate_article.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    page_width, page_height = letter  # Create local variables instead of unpacking directly
    
    # Add text content
    text_object = c.beginText(50, page_height - 50)
    text_object.setFont("Helvetica", 12)
    
    for line in SAMPLE_TEXT:
        if line.startswith("# "):
            # Handle heading
            text_object.setFont("Helvetica-Bold", 16)
            text_object.textLine(line[2:])
            text_object.setFont("Helvetica", 12)
        else:
            # Handle normal text, wrapping at 70 chars
            if not line:
                text_object.textLine("")
            else:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 > 70:
                        text_object.textLine(current_line)
                        current_line = word
                    else:
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                if current_line:
                    text_object.textLine(current_line)
    
    c.drawText(text_object)
    c.save()
    
    print(f"Created sample PDF at {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    create_sample_pdf()
