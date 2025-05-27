"""
Create a sample PDF file for testing the SocioGraph application.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_sample_pdf():
    """Create a sample PDF file with climate change content."""
    output_path = Path("d:/sociorag/input/climate_article.pdf")
    output_path.parent.mkdir(exist_ok=True)
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Set up the document
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Climate Change: An Overview")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 90, "Introduction")
    
    c.setFont("Helvetica", 12)
    text = """
    Climate change refers to long-term shifts in temperatures and weather patterns. 
    These shifts may be natural, but since the 1800s, human activities have been the 
    main driver of climate change, primarily due to the burning of fossil fuels like coal, 
    oil, and gas, which produces heat-trapping gases.
    """
    y_position = height - 120
    for line in text.strip().split('\n'):
        c.drawString(50, y_position, line.strip())
        y_position -= 15
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position - 30, "Key Impacts")
    
    c.setFont("Helvetica", 12)
    impacts = [
        "Rising global temperatures",
        "Sea level rise",
        "Increased frequency of extreme weather events",
        "Changes in precipitation patterns",
        "Threats to biodiversity and ecosystems",
        "Effects on human health and agriculture"
    ]
    
    y_position -= 60
    for impact in impacts:
        c.drawString(70, y_position, "• " + impact)
        y_position -= 20
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position - 30, "Mitigation Strategies")
    
    c.setFont("Helvetica", 12)
    strategies = [
        "Transition to renewable energy sources",
        "Improve energy efficiency",
        "Sustainable transportation systems",
        "Reforestation and forest conservation",
        "Reduce, reuse, and recycle materials",
        "Policy changes and international cooperation"
    ]
    
    y_position -= 60
    for strategy in strategies:
        c.drawString(70, y_position, "• " + strategy)
        y_position -= 20
    
    c.save()
    print(f"Sample PDF created successfully at {output_path}")
    return output_path

if __name__ == "__main__":
    create_sample_pdf()
