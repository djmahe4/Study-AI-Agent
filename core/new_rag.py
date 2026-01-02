import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np
from icecream import ic
import tqdm
ic.disable()


def ocr_page(page):
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    ocr_lines = []
    high=[]
    prob=""

    for i, text in enumerate(data["text"]):
        if text.strip():
            #ic(data)
            try:
                if data["text"][i+1]=="" and data["text"][i+2]=="":
                    for j in range(10):
                        if text==' ':
                            break
                        prob+=data["text"][i+j]+" "
                if not prob=="":
                    if data["word_num"][i]>data["word_num"][i-1]+1:
                        break
                    high.append(prob.strip())
                ic(data["word_num"][i],text)
                prob=""
            except:
                pass
            wn=0
            ocr_lines.append({
                "text": text.strip(),
                "x": data["left"][i],
                "y": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i]
            })
    # ic(data.keys())
    ic(high)
    # #ic(data)
    # exit(0)
    new_hight=[i for h in high for i in h.split()]
    no_dup=[]
    for i in range(len(new_hight)):
        try:
            if new_hight[i] ==new_hight[i+1]:
                continue
            else:
                no_dup.append(new_hight[i])
        except:
            pass
    del(new_hight)
    new_hight=no_dup
    ic(new_hight)
    # ic([i for i in new_hight if len(i)>1])
    # exit(0)
    return ocr_lines,[i for i in new_hight if len(i)>1]


def looks_like_heading(text):
    if len(text) < 3: return False
    if text.isdigit(): return False
    # heuristics for headings
    if text.istitle() or text.isupper():
        return True
    return False


def extract_topics_scanned(pdf_path):
    doc = fitz.open(pdf_path)
    topic_ranges = {}
    for tqdm_page in tqdm.tqdm(range(len(doc)), desc="Processing pages"):
        page = doc[tqdm_page]
        page_num = tqdm_page + 1
    #for page_num, page in enumerate(doc, start=1):
        # raw = page.get_text("dict")["blocks"]
        # has_text = any("text" in span for blk in raw if blk["type"] == 0 for line in blk.get("lines", []) for span in
        #                line.get("spans", []))
        # print(raw)
        # # If no real text found → OCR
        # if not has_text:
        lines,high = ocr_page(page)
        # else:
        #     # Use PyMuPDF normal text (more reliable)
        #     lines = []
        #     for blk in raw:
        #         if blk["type"] != 0: continue
        #         for line in blk["lines"]:
        #             for span in line["spans"]:
        #                 lines.append({
        #                     "text": span["text"].strip(),
        #                     "y": line["bbox"][1],
        #                     "height": span.get("size", 10)
        #                 })

        # new_topic_found = False
        # text_lines = [l for l in lines if l["text"].strip()]
        #
        # if not text_lines:
        #     continue
        #
        # # Compute average text height
        # avg_height = np.mean([l.get("height", 0) for l in text_lines if l.get("height", 0) > 0])
        #
        # for line in text_lines:
        #     txt = line["text"]
        #     size = line.get("height", 10)
        #
        #     # Heading heuristic: larger than avg OR formatted like a heading
        #     if size >= avg_height * 1.25 or looks_like_heading(txt):
        #         current_topic = txt
        #         topic_ranges[current_topic] = {"start": page_num, "end": page_num}
        #         new_topic_found = True
        #         break
        #
        # if not new_topic_found and current_topic:
        #     topic_ranges[current_topic]["end"] = page_num
        for line in high:
            txt = line
            # Heading heuristic: larger than avg OR formatted like a heading
            if looks_like_heading(txt):
                current_topic = txt
                # topic_ranges[current_topic] = {"start": page_num, "end": page_num}
                if current_topic not in topic_ranges:
                    topic_ranges[current_topic] = []
                topic_ranges[current_topic].append(page_num)
                #break
        if current_topic in topic_ranges:
            topic_ranges[current_topic].append(page_num+1)
    return topic_ranges
if __name__ == "__main__":
    pdf_path = r"D:\S5\COMPUTER NETWORKS\Notes\CN MODULE FIVE.pdf"  # Replace with your PDF file path
    topic_ranges = extract_topics_scanned(pdf_path)
    for topic, ranges in topic_ranges.items():
        print(f"Topic: {topic}, Pages: {ranges['start']} - {ranges['end']}")