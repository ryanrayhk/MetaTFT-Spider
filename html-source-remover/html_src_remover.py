# to run:
# python html-source-remover/html_src_remover.py input file
# python html-source-remover/html_src_remover.py data-sample/timeline-stage1-3.txt
import os
import re
from bs4 import BeautifulSoup
import argparse

def remove_attributes_and_svg(content):
    """
    Remove src and style attributes from HTML content and clean SVG elements.
    
    Args:
        content (str): The content to process
        
    Returns:
        str: Processed content
    """
    try:
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all elements with src or style attributes
        for tag in soup.find_all(attrs={'src': True, 'style': True}):
            # Remove both src and style attributes
            del tag['src']
            del tag['style']
        
        # Find elements with only src attribute
        for tag in soup.find_all(attrs={'src': True}):
            del tag['src']
            
        # Find elements with only style attribute
        for tag in soup.find_all(attrs={'style': True}):
            del tag['style']
            
        # Handle SVG elements
        for svg in soup.find_all('svg'):
            if not svg.has_attr('class'):
                # Remove SVG elements without class
                svg.decompose()
            else:
                # Keep only the class attribute
                class_value = svg['class']
                svg.attrs.clear()
                svg['class'] = class_value
                svg.clear()  # Remove children
        
        return str(soup)
        
    except Exception as e:
        print(f"Error processing content: {str(e)}")
        return content

def remove_html_src(input_file, output_file=None):
    """
    Remove src and style attributes from HTML content in a file and clean SVG elements.
    
    Args:
        input_file (str): Path to the input file
        output_file (str, optional): Path to the output file. If not provided, will overwrite input file.
    """
    try:
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process the content
        processed_content = remove_attributes_and_svg(content)
        
        # Determine output file
        if output_file is None:
            output_file = input_file
        
        # Write the cleaned content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)
            
        print(f"Successfully processed {input_file}")
        print(f"Output saved to {output_file}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Remove src and style attributes from HTML content and clean SVG elements')
    parser.add_argument('input_file', help='Input file path')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    remove_html_src(args.input_file, args.output)

if __name__ == "__main__":
    main() 