"""
Create a sample PDF file for testing purposes.
This script generates a simple PDF document about climate change for testing.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pathlib import Path

def create_climate_article_pdf():
    output_dir = Path("d:/sociorag/input")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "climate_article.pdf"
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Set font and size for title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Climate Change: A Global Challenge")
    
    # Set font and size for body text
    c.setFont("Helvetica", 12)
    
    # First paragraph
    text = """
    Climate change refers to long-term shifts in temperatures and weather patterns. 
    These shifts may be natural, such as through variations in the solar cycle. But since 
    the 1800s, human activities have been the main driver of climate change, primarily due 
    to burning fossil fuels like coal, oil and gas.
    """
    y_position = height - 100
    for line in text.strip().split('\n'):
        c.drawString(72, y_position, line.strip())
        y_position -= 15
    
    # Second paragraph
    text = """
    Burning fossil fuels generates greenhouse gas emissions that act like a blanket wrapped 
    around the Earth, trapping the sun's heat and raising temperatures. Examples of greenhouse 
    gas emissions that are causing climate change include carbon dioxide and methane.
    """
    y_position -= 10
    for line in text.strip().split('\n'):
        c.drawString(72, y_position, line.strip())
        y_position -= 15
    
    # Third paragraph
    text = """
    The impacts of climate change are already being felt around the world. Rising global 
    temperatures have been accompanied by changes in weather and climate. Many places have 
    seen changes in rainfall, resulting in more floods, droughts, or intense rain, as well 
    as more frequent and severe heat waves.
    """
    y_position -= 10
    for line in text.strip().split('\n'):
        c.drawString(72, y_position, line.strip())
        y_position -= 15
    
    # Fourth paragraph
    text = """
    Solutions to climate change include mitigation strategies like reducing emissions, 
    transitioning to renewable energy, and adaptation measures to deal with the impacts 
    that are already happening. Global cooperation and individual actions are both 
    crucial in addressing this challenge.
    """
    y_position -= 10
    for line in text.strip().split('\n'):
        c.drawString(72, y_position, line.strip())
        y_position -= 15
    
    c.save()
    print(f"Climate article PDF created at {output_path}")
    return output_path

if __name__ == "__main__":
    create_climate_article_pdf()
