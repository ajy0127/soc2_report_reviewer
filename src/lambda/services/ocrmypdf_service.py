import subprocess
import tempfile
import os
import logging
from pathlib import Path
import PyPDF2
from io import BytesIO
import io
import shutil
import re
import pymupdf4llm

logger = logging.getLogger(__name__)

class OCRmyPDFService:
    """Service for extracting text from documents using PyMuPDF4LLM with PyPDF2 as fallback."""
    
    def __init__(self):
        # Configuration options for text extraction
        self.options = {
            'language': 'eng',  # Default language
            'deskew': True,     # Auto-straighten pages
            'clean': False,     # Clean pages before OCR (might remove content)
            'rotate_pages': True, # Auto-rotate pages
            'optimize': 1       # Level 1 optimization
        }
        
        # Flag to indicate if OCRmyPDF is available
        self.ocrmypdf_available = self._check_ocrmypdf_available()
        
        # Initialize OCRmyPDF version
        self.ocrmypdf_version = self._check_ocrmypdf_version()
    
    def _check_ocrmypdf_available(self):
        """Check if OCRmyPDF is available on the system."""
        try:
            result = subprocess.run(
                ['ocrmypdf', '--version'],
                capture_output=True,
                text=True
            )
            logger.info(f"OCRmyPDF version: {result.stdout.strip()}")
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("OCRmyPDF not available, falling back to PyMuPDF4LLM and PyPDF2 for text extraction")
            return False
    
    def _check_ocrmypdf_version(self):
        """Check if OCRmyPDF is installed and get its version."""
        try:
            # Check if OCRmyPDF is installed
            version_output = subprocess.check_output(["ocrmypdf", "--version"], stderr=subprocess.STDOUT, text=True)
            match = re.search(r"(\d+\.\d+\.\d+)", version_output)
            if match:
                return match.group(1)
            else:
                logger.warning("OCRmyPDF installed but version unknown")
                return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.warning(f"OCRmyPDF not installed or not found: {str(e)}")
            return None
    
    def extract_text(self, pdf_content):
        """
        Extract text from a PDF using PyMuPDF4LLM as primary method, with OCRmyPDF and PyPDF2 as fallbacks.
        
        Args:
            pdf_content (bytes): The PDF file content in bytes
            
        Returns:
            str: The extracted text from the document
            
        Raises:
            Exception: If text extraction fails
        """
        try:
            # First try with PyMuPDF4LLM
            try:
                logger.info("Attempting to extract text with PyMuPDF4LLM")
                return self._extract_with_pymupdf(pdf_content)
            except Exception as e:
                logger.warning(f"PyMuPDF4LLM extraction failed: {str(e)}. Trying next method.")
            
            # If PyMuPDF4LLM fails and OCRmyPDF is available, try that
            if self.ocrmypdf_available:
                try:
                    logger.info("Attempting to extract text with OCRmyPDF")
                    return self._extract_with_ocrmypdf(pdf_content)
                except Exception as e:
                    logger.warning(f"OCRmyPDF extraction failed: {str(e)}. Falling back to PyPDF2 with repair.")
            else:
                logger.info("OCRmyPDF not available, skipping to PyPDF2")
            
            # Finally, try PyPDF2 with repair
            try:
                logger.info("Attempting PyPDF2 extraction with repair")
                return self._extract_with_pypdf2_repair(pdf_content)
            except Exception as repair_e:
                error_msg = f"All extraction methods failed. Last error: {str(repair_e)}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"Error extracting text: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _extract_with_pymupdf(self, pdf_content):
        """Extract text using PyMuPDF4LLM."""
        logger.info("Starting text extraction with PyMuPDF4LLM")
        
        try:
            # Write PDF content to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_path = temp_file.name
            
            # Try different extraction approaches
            
            # 1. First try the standard to_markdown approach
            try:
                logger.info("Attempting PyMuPDF4LLM to_markdown extraction")
                md_text = pymupdf4llm.to_markdown(temp_path, page_chunks=True)
                
                # Combine all pages into a single string
                if isinstance(md_text, list):
                    text_parts = []
                    for i, page in enumerate(md_text):
                        text_parts.append(f"--- Page {i+1} ---")
                        page_text = page.get("text", "")
                        text_parts.append(page_text if page_text else "[No text on this page]")
                    
                    full_text = "\n\n".join(text_parts)
                else:
                    full_text = md_text
                
                if full_text and len(full_text.strip()) > 100:  # Check if we got meaningful content
                    logger.info(f"Successfully extracted {len(full_text)} characters of text with PyMuPDF4LLM to_markdown")
                    return full_text
                else:
                    logger.warning("PyMuPDF4LLM to_markdown extraction yielded insufficient text, trying alternative methods")
            except Exception as e:
                logger.warning(f"PyMuPDF4LLM to_markdown extraction failed: {str(e)}, trying alternative methods")
            
            # 2. Try direct PyMuPDF extraction
            try:
                import fitz  # PyMuPDF
                logger.info("Attempting direct PyMuPDF extraction")
                
                doc = fitz.open(temp_path)
                text_parts = []
                
                for i, page in enumerate(doc):
                    text_parts.append(f"--- Page {i+1} ---")
                    page_text = page.get_text()
                    text_parts.append(page_text if page_text else "[No text on this page]")
                
                doc.close()
                full_text = "\n\n".join(text_parts)
                
                if full_text and len(full_text.strip()) > 100:  # Check if we got meaningful content
                    logger.info(f"Successfully extracted {len(full_text)} characters of text with direct PyMuPDF")
                    return full_text
                else:
                    logger.warning("Direct PyMuPDF extraction yielded insufficient text, trying next method")
            except Exception as e:
                logger.warning(f"Direct PyMuPDF extraction failed: {str(e)}, trying next method")
            
            # 3. Try PyMuPDF with OCR mode
            try:
                import fitz  # PyMuPDF
                logger.info("Attempting PyMuPDF extraction with OCR hints")
                
                doc = fitz.open(temp_path)
                text_parts = []
                
                for i, page in enumerate(doc):
                    text_parts.append(f"--- Page {i+1} ---")
                    # Try to get text with different extraction flags
                    page_text = page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_DEHYPHENATE)
                    text_parts.append(page_text if page_text else "[No text on this page]")
                
                doc.close()
                full_text = "\n\n".join(text_parts)
                
                if full_text and len(full_text.strip()) > 100:  # Check if we got meaningful content
                    logger.info(f"Successfully extracted {len(full_text)} characters of text with PyMuPDF OCR hints")
                    return full_text
                else:
                    logger.warning("PyMuPDF extraction with OCR hints yielded insufficient text")
                    # If we got here, all PyMuPDF methods failed to extract meaningful text
                    raise Exception("All PyMuPDF extraction methods failed to extract meaningful text")
            except Exception as e:
                logger.warning(f"PyMuPDF extraction with OCR hints failed: {str(e)}")
                raise Exception(f"All PyMuPDF extraction methods failed: {str(e)}")
                
        except Exception as e:
            error_msg = f"Error extracting text with PyMuPDF4LLM: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        finally:
            # Clean up temporary file
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _extract_with_ocrmypdf(self, pdf_content):
        """Extract text using OCRmyPDF."""
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as input_file, \
             tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as output_file:
            
            # Write the PDF content to the input file
            input_file.write(pdf_content)
            input_file.flush()
            
            # Close the files to ensure they're accessible by OCRmyPDF
            input_path = input_file.name
            output_path = output_file.name
        
        try:
            # Build OCRmyPDF command
            cmd = [
                'ocrmypdf',
                '--force-ocr',  # Force OCR even if text exists
                '--output-type', 'pdf',
                '--quiet',
            ]
            
            # Add options
            if self.options['language']:
                cmd.extend(['-l', self.options['language']])
            if self.options['deskew']:
                cmd.append('--deskew')
            if self.options['clean']:
                cmd.append('--clean')
            if self.options['rotate_pages']:
                cmd.append('--rotate-pages')
            if self.options['optimize']:
                cmd.extend(['--optimize', str(self.options['optimize'])])
                
            # Add input and output file paths
            cmd.extend([input_path, output_path])
            
            # Run OCRmyPDF
            logger.info(f"Running OCRmyPDF command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("OCRmyPDF processing completed successfully")
            
            # Extract text from the OCR'd PDF using PyPDF2
            extracted_text = self._extract_with_pypdf2(open(output_path, 'rb').read())
            
            return extracted_text
            
        except subprocess.CalledProcessError as e:
            # Log error details
            error_msg = f"OCRmyPDF processing failed: {str(e)}"
            if e.stdout:
                error_msg += f"\nStdout: {e.stdout}"
            if e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            logger.error(error_msg)
            
            # Re-raise to be caught by the extract_text method
            raise Exception(error_msg)
            
        finally:
            # Clean up temporary files
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def _extract_with_pypdf2(self, pdf_content):
        """Extract text using PyPDF2."""
        logger.info("Starting text extraction with PyPDF2")
        
        extracted_text = ""
        pdf_file = BytesIO(pdf_content)
        
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    extracted_text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
                else:
                    logger.warning(f"No text extracted from page {page_num + 1}")
                    extracted_text += f"--- Page {page_num + 1} ---\n[No text content detected]\n\n"
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters of text with PyPDF2")
            return extracted_text
        
        except Exception as e:
            error_msg = f"Error extracting text with PyPDF2: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _extract_with_pypdf2_repair(self, pdf_content):
        """
        Extract text from a PDF document using PyPDF2 with repair attempts for corrupted PDFs.
        
        Args:
            pdf_content (bytes): The PDF document content.
            
        Returns:
            str: The extracted text from the PDF.
        """
        logger.info("Attempting to repair and extract text from potentially corrupted PDF")
        
        try:
            # First repair attempt - using PyPDF2 strict=False
            pdf_file = io.BytesIO(pdf_content)
            try:
                # Try with more lenient parsing
                pdf_reader = PyPDF2.PdfReader(pdf_file, strict=False)
                
                text_parts = []
                for i, page in enumerate(pdf_reader.pages):
                    text_parts.append(f"--- Page {i+1} ---")
                    try:
                        text = page.extract_text()
                        text_parts.append(text if text else "[No text on this page]")
                    except Exception as page_e:
                        logger.warning(f"Error extracting text from page {i+1}: {str(page_e)}")
                        text_parts.append(f"[Error extracting text from page {i+1}]")
                
                full_text = "\n".join(text_parts)
                if len(full_text.strip()) > 100:  # Ensure we have meaningful content
                    logger.info(f"Successfully extracted {len(full_text)} characters of text with PyPDF2 repair")
                    return full_text
                else:
                    logger.warning("Repair attempt yielded insufficient text")
                
            except Exception as e:
                logger.warning(f"First repair attempt failed: {str(e)}")
            
            # Second repair attempt - try parsing page by page
            logger.info("Attempting page-by-page extraction")
            pdf_file.seek(0)
            
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file, strict=False)
                text_parts = []
                
                # Try to access each page individually
                for i in range(len(pdf_reader.pages)):
                    try:
                        text_parts.append(f"--- Page {i+1} ---")
                        page = pdf_reader.pages[i]
                        text = page.extract_text()
                        text_parts.append(text if text else "[No text on this page]")
                    except Exception as page_e:
                        logger.warning(f"Error accessing page {i+1}: {str(page_e)}")
                        text_parts.append(f"[Error accessing page {i+1}]")
                
                full_text = "\n".join(text_parts)
                logger.info(f"Successfully extracted {len(full_text)} characters with page-by-page approach")
                return full_text
                
            except Exception as e:
                logger.warning(f"Page-by-page extraction failed: {str(e)}")
            
            # Last resort - try to extract any text possible
            logger.warning("All PyPDF2 repair attempts failed. Returning minimal text.")
            return "Failed to extract text from corrupted PDF. Please check the document's integrity."
            
        except Exception as e:
            error_msg = f"All PDF repair attempts failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) 