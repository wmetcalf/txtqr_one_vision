import os
import sys
import cv2
import html
import magic
import argparse
import json
from PIL import Image, ImageDraw
from bs4 import BeautifulSoup
import tempfile
import traceback
from pathlib import Path
import logging
import uuid

logger = logging.getLogger(__name__)

try:
    import extract_msg

    HAVE_EXTRACT_MSG = True
except ImportError:
    logger.warning("The 'extract_msg' library is required for handling .msg files. Install it using 'pip install extract-msg'")
    HAVE_EXTRACT_MSG = False
try:
    import re2 as re
except ImportError:
    import re

try:
    from magika import Magika

    HAVE_MAGIKA = True
except ImportError:
    logger.warning(
        "The 'magika' library won't be used for file type detection. Install it using 'pip install magika' does better at detecting eml's than libmagic"
    )
    HAVE_MAGIKA = False


class QRCodeTXTExtractor:
    def __init__(self, output_dir, model_dir, decoder="none"):
        if HAVE_MAGIKA:
            self.magika = Magika()
        self.decoder = decoder
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir
        self.results = []
        self.decode_qr = False
        if self.decoder == "bft_qr_reader":
            try:
                from bft_qr_reader.bft_qr_reader import BFTQRCodeReader

                self.bft_qr_decoder = BFTQRCodeReader(wechat_model_dir=model_dir)
                self.decode_qr = True
            except ImportError:
                logger.debug(
                    "The 'bft_qr_reader' library is required for QR code detection. Install it using 'sudo apt-get install -y libzbar0 inkscape librsvg2-bin && pip3 install git+https://github.com/wmetcalf/bft_qr_reader.git'"
                )
        elif self.decoder == "zxing":
            try:
                import zxingcpp

                self.zxing_decoder = zxingcpp
                self.decode_qr = True
            except ImportError:
                logger.debug(
                    "The 'zxing-cpp' library is required for QR code detection using zxing-cpp. Install it using 'pip install zxing-cpp'"
                )
        else:
            logger.debug(f"Unsupported decoder or none specified won't do qr_decodes: {self.decoder}")
            self.decode_qr = False

        if not self.decode_qr:
            logger.debug("We won't be doing qr decodes only image generation")

        self.char_to_modules = {
            "█": [[1, 1], [1, 1]],
            " ": [[0, 0], [0, 0]],
            "▀": [[1, 1], [0, 0]],
            "▄": [[0, 0], [1, 1]],
            "▌": [[1, 0], [1, 0]],
            "▐": [[0, 1], [0, 1]],
            "▖": [[0, 0], [1, 0]],
            "▗": [[0, 0], [0, 1]],
            "▘": [[1, 0], [0, 0]],
            "▝": [[0, 1], [0, 0]],
            "▞": [[0, 1], [1, 0]],
            "▟": [[1, 1], [1, 0]],
            "■": [[1, 1], [1, 1]],
            "□": [[0, 0], [0, 0]],
            "#": [[1, 1], [1, 1]],
            "@": [[1, 1], [1, 1]],
            "▓": [[1, 1], [1, 1]],
            "▇": [[1, 1], [1, 1]],
            "▆": [[1, 1], [1, 1]],
            "▅": [[1, 1], [1, 1]],
            "▃": [[1, 1], [1, 1]],
            "▂": [[1, 1], [1, 1]],
            "▁": [[1, 1], [1, 1]],
        }

    def ascii_cleanup(self, text):
        if re.search(r'\x1B',text):
            try:
                eat_it = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
                new_text = eat_it.sub('', text)
                return(new_text)
            except:
                pass
        return text

    def decode_qr_codes(self, image_path):
        if self.decoder == "bft_qr_reader":
            return self.decode_with_bft(image_path)
        elif self.decoder == "zxing":
            return self.decode_with_zxing_cpp(image_path)
        else:
            logger.debug(f"Unsupported decoder: {self.decoder}")
            return None

    def decode_with_bft(self, image_path):
        try:
            logger.debug(f"Decoding QR code with BFT in image {image_path}")
            tmp_dict = {}
            tmp_dict["message"] = self.bft_qr_decoder.enhance_and_decode(image_path, self.output_dir, False, False)
            decoded_texts = []
            if "message" in tmp_dict and isinstance(tmp_dict["message"], list):
                for message in tmp_dict["message"]:
                    decoded_text = message.get("decoded_text", "")
                    if decoded_text:
                        decoded_texts.append(decoded_text)
            return decoded_texts
        except Exception as e:
            logger.debug(f"Exception occurred while decoding with qreader: {e}")
            traceback.print_exc()
            return []

    def decode_with_zxing_cpp(self, image_path):
        try:
            logger.debug(f"Decoding QR code with zxing-cpp in image {image_path}")
            decoded_texts = []
            image = cv2.imread(image_path)
            decoded_objects = self.zxing_decoder.read_barcodes(image)
            for obj in decoded_objects:
                decoded_texts.append(obj.text)
            return decoded_texts
        except Exception as e:
            logger.debug(f"Exception occurred while decoding with zxing-cpp: {e}")
            return []

    def detect_file_encoding(self, file_path):
        """https://www.youtube.com/watch?v=hbh3XBwo9k4"""
        with open(file_path, "rb") as f:
            raw = f.read(4)
        if raw.startswith(b"\xff\xfe\x00\x00"):
            encoding = "utf-32-le"
        elif raw.startswith(b"\x00\x00\xfe\xff"):
            encoding = "utf-32-be"
        elif raw.startswith(b"\xfe\xff"):
            encoding = "utf-16-be"
        elif raw.startswith(b"\xff\xfe"):
            encoding = "utf-16-le"
        elif raw.startswith(b"\xef\xbb\xbf"):
            encoding = "utf-8-sig"
        else:
            encoding = "utf-8"
        return encoding

    def read_text_file(self, file_path):
        encoding = self.detect_file_encoding(file_path)
        # logger.debug(f"Detected encoding: {encoding}")

        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            text = f.read()

        return text

    def read_eml_file(self, file_path):
        from email import policy
        from email.parser import BytesParser

        with open(file_path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)

        text = ""
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ["text/plain", "text/html"]:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset()
                if payload is not None:
                    if charset:
                        payload = payload.decode(charset, errors="replace")
                    else:
                        payload = payload.decode(errors="replace")
                    text += payload + "\n"
                if content_type == "text/html":
                    text = self.extract_ascii_qrcode_from_html(text)
        return text

    def read_msg_file(self, file_path):
        msg = extract_msg.Message(file_path)
        text = ""
        if msg.body:
            text += msg.body + "\n"
        if msg.htmlBody:
            text += msg.htmlBody + "\n"
            text = self.extract_ascii_qrcode_from_html(text)
        return text

    def extract_ascii_qrcode_from_html(self, html_content):
        ascii_qrcode = ""
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n")
        text = html.unescape(text)
        ascii_qrcode += text + "\n"
        return ascii_qrcode.rstrip()

    def detect_ascii_qrcode(self, text, min_lines=15, blank_line_reset=4):
        text = self.ascii_cleanup(text)
        pattern = re.compile(r"^[{} \s]+$".format("".join(re.escape(ch) for ch in self.char_to_modules.keys())))
        non_space_pattern = re.compile(r"[{}]+".format("".join(re.escape(ch) for ch in self.char_to_modules.keys())))
        lines = text.split("\n")
        qrcode_blocks = []
        current_block = []
        is_qrcode = False
        blank_line_count = 0  # To track how many blank lines we have seen

        for line in lines:
            stripped_line = line.rstrip()

            if not stripped_line.strip():
                blank_line_count += 1
                if blank_line_count >= blank_line_reset and is_qrcode:
                    if len(current_block) >= min_lines:
                        qrcode_blocks.append(current_block)
                    current_block = []
                    is_qrcode = False
                continue

            if pattern.match(stripped_line) and non_space_pattern.search(stripped_line):
                current_block.append(stripped_line)
                is_qrcode = True
                blank_line_count = 0
            else:

                blank_line_count = 0

        if is_qrcode and len(current_block) >= min_lines:
            qrcode_blocks.append(current_block)

        return qrcode_blocks

    def render_qrcode(self, qrcode_lines, output_file="qrcode.png"):
        if not qrcode_lines:
            return False

        module_size = 10

        qr_matrix = []
        for line in qrcode_lines:
            row_top = []
            row_bottom = []
            for char in line:
                modules = self.char_to_modules.get(char)
                if modules:
                    row_top.extend(modules[0])
                    row_bottom.extend(modules[1])
                else:
                    row_top.extend([0, 0])
                    row_bottom.extend([0, 0])
            qr_matrix.append(row_top)
            qr_matrix.append(row_bottom)

        height = len(qr_matrix)
        width = len(qr_matrix[0]) if qr_matrix else 0

        img = Image.new("RGB", (width * module_size, height * module_size), "white")
        draw = ImageDraw.Draw(img)

        for y, row in enumerate(qr_matrix):
            for x, module in enumerate(row):
                if module == 1:
                    x0 = x * module_size
                    y0 = y * module_size
                    x1 = x0 + module_size - 1
                    y1 = y0 + module_size - 1
                    draw.rectangle([x0, y0, x1, y1], fill="black")

        img.save(output_file)
        return True

    def get_file_mime_type(self, filename):
        mime_type = None
        if HAVE_MAGIKA:
            file_path = Path(filename)
            res = self.magika.identify_path(file_path)
            mime_type = res.output.mime_type
            # Magika seems to suck at text files but is good at EML's
            if not any(x in mime_type for x in ["text/", "txt", "outlook", "rfc822"]):
                try:
                    mime = magic.Magic(mime=True)
                    mime_type = mime.from_file(filename)
                except Exception as e:
                    logger.debug(f"Error detecting MIME type: {e}")
                    return mime_type
        else:
            try:
                mime = magic.Magic(mime=True)
                mime_type = mime.from_file(filename)
                return mime_type
            except Exception as e:
                logger.debug(f"Error detecting MIME type: {e}")
                return mime_type
        return mime_type

    def seek_and_destroy(self, file_input, reset_results=False, output_dir=None):
        """https://www.youtube.com/watch?v=FLTchCiC0T0"""
        file_path = None
        temp_file_path = None
        if reset_results:
            self.results = []
        result = {"file": file_path, "mime_type": None, "qrcode_images": [], "decoding_results": [], "errors": []}
        try:
            if output_dir is None:
                output_dir = self.output_dir
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    logger.debug(f"Error creating output directory: {e}")
                    result["errors"].append(f"Error creating output directory: {e}")
                    self.results.append(result)
                    return result

            if isinstance(file_input, bytes):
                with tempfile.NamedTemporaryFile(delete=False, dir=output_dir) as temp_file:
                    temp_file.write(file_input)
                    temp_file_path = temp_file.name
                    result["file"] = temp_file_path
                    file_path = temp_file_path
            elif isinstance(file_input, str):
                file_path = file_input
                if os.path.isfile(file_path):
                    result["file"] = file_path
                else:
                    result["file"] = file_path
                    result["errors"].append(f"File not found: {file_path}")
                    self.results.append(result)
                    return result
            else:
                result["errors"].append("Invalid file input type. Must be either a file path or bytes.")
                self.results.append(result)
                return result
            mime_type = self.get_file_mime_type(file_path)
            result["mime_type"] = mime_type
            if mime_type is None:
                result["errors"].append("Could not determine the file type.")
                self.results.append(result)
                return result
            if (
                mime_type in ["message/rfc822", "application/vnd.ms-outlook"]
                or file_path.lower().endswith(".eml")
                or file_path.lower().endswith(".msg")
            ):
                if mime_type == "message/rfc822" or file_path.lower().endswith(".eml"):
                    ascii_qrcode = self.read_eml_file(file_path)
                elif mime_type == "application/vnd.ms-outlook" or file_path.lower().endswith(".msg"):
                    if HAVE_EXTRACT_MSG:
                        ascii_qrcode = self.read_msg_file(file_path)
                    else:
                        result["errors"].append("msg file found but extract_msg not installed")
                        self.results.append(result)
                        return
            elif mime_type == "text/html":
                with open(file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    ascii_qrcode = self.extract_ascii_qrcode_from_html(html_content)
            elif "text/plain" in mime_type:
                ascii_qrcode = self.read_text_file(file_path)
            else:
                result["errors"].append(f"Unsupported MIME type: {mime_type}")
                self.results.append(result)
                return result

            if not ascii_qrcode:
                result["errors"].append("No ASCII QR code found in the content.")
                self.results.append(result)
                return result

            qrcode_blocks = self.detect_ascii_qrcode(ascii_qrcode, min_lines=15)
            if not qrcode_blocks:
                result["errors"].append("No QR code detected in the extracted text.")
                self.results.append(result)
                return result

            for idx, qrcode_lines in enumerate(qrcode_blocks):
                output_file = os.path.join(output_dir, f"{str(uuid.uuid4())}.png")
                success = self.render_qrcode(qrcode_lines, output_file)
                if success:
                    result["qrcode_images"].append(output_file)
                    if self.decode_qr:
                        logger.debug(f"Decoding QR code in image {output_file}")
                        decoded_texts = self.decode_qr_codes(output_file)
                        if decoded_texts:
                            result["decoding_results"].extend(decoded_texts)
                        else:
                            result["errors"].append(f"No QR code detected in image {output_file}.")
                else:
                    result["errors"].append(f"Failed to render QR code for block {idx+1}.")
        except Exception as e:
            result["errors"].append(f"Exception occurred: {str(e)}")
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        self.results.append(result)
        return result

    def save_results(self, output_path):
        with open(os.path.join(self.output_dir, "results.json"), "w", encoding="utf-8") as json_file:
            logger.debug(self.results)
            json.dump(self.results, json_file, ensure_ascii=False, indent=4)


def main():
    parser = argparse.ArgumentParser(
        description="ASCII/Unicode EML/HTML/TXT/MSG QRCode Seek and Destroy https://www.youtube.com/watch?v=FLTchCiC0T0"
    )
    parser.add_argument("-i", "--input", required=True, help="Input file or directory")
    parser.add_argument(
        "--decoder", choices=["bft_qr_reader", "none", "zxing"], default="zxing", help="Decoder to use (bft_qr_reader or zxing) or none"
    )
    parser.add_argument("-o", "--output", default="./", help="Output directory")
    parser.add_argument("--model_dir", default=None, help="Path to wechat model dir")
    parser.add_argument(
        "-l",
        "--log_level",
        required=False,
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level. Default is DEBUG.",
    )
    args = parser.parse_args()
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        logger.error(f"Invalid log level {args.log_level}")
        sys.exit(1)
    logging.basicConfig(level=numeric_level)
    # logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    input_path = args.input

    extractor = QRCodeTXTExtractor(args.output, args.model_dir, decoder=args.decoder)

    if os.path.isfile(input_path):
        files = [input_path]
    elif os.path.isdir(input_path):
        files = [os.path.join(input_path, f) for f in os.listdir(input_path)]
    else:
        logger.debug(f"Input path {input_path} is not a valid file or directory.")
        return

    for file_path in files:
        extractor.seek_and_destroy(file_path, False)

    extractor.save_results(args.output)

    logger.debug(f"Results have been written to {args.output}")


if __name__ == "__main__":
    main()
