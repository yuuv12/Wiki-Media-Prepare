import json
import os
import argparse
from mwparserfromhell import parse
from tqdm import tqdm
from opencc import OpenCC

class WikiCleaner:
    def __init__(self, input_dir, output_file, max_docs=1000, min_length=100, convert_mode='t2s'):
        self.input_dir = input_dir
        self.output_file = output_file
        self.max_docs = max_docs
        self.min_length = min_length
        self.converter = OpenCC("t2s")
        self.count = 0
        self.skipped = 0
        self.keys = set()

    def clean_text(self, text):
        wikicode = parse(text)
        cleaned = wikicode.strip_code().strip()
        if self.converter:
            cleaned = self.converter.convert(cleaned)
        return cleaned

    def clean_title(self, title):
        return self.converter.convert(title) if self.converter else title

    def is_valid_title(self, title):
        return not any(title.startswith(ns) for ns in ["分类:", "Wikipedia:", "模板:", "File:"])

    def process(self):
        with open(self.output_file, 'w', encoding='utf-8') as fout:
            for root, _, files in os.walk(self.input_dir):
                for fname in sorted(files):
                    if not fname.startswith('wiki_'):
                        continue
                    fpath = os.path.join(root, fname)
                    with open(fpath, 'r', encoding='utf-8') as f:
                        for line in f:
                            if self.max_docs > 0 and self.count >= self.max_docs:
                                return
                            try:
                                page = json.loads(line)
                                self.keys.update(page.keys())

                                title = page.get("title", "")
                                if not self.is_valid_title(title):
                                    self.skipped += 1
                                    continue

                                text_raw = page.get("text", "")
                                text_cleaned = self.clean_text(text_raw)
                                title_cleaned = self.clean_title(title)

                                if len(text_cleaned) < self.min_length:
                                    self.skipped += 1
                                    continue

                                meta_fields = {k: v for k, v in page.items() if k != "text"}
                                meta_fields["title"] = title_cleaned
                                meta_fields["url"] = f"https://zh.wikipedia.org/wiki/{title_cleaned.replace(' ', '_')}"

                                out_data = {
                                    "text": text_cleaned,
                                    "meta": meta_fields
                                }

                                fout.write(json.dumps(out_data, ensure_ascii=False) + "\n")
                                self.count += 1
                            except Exception:
                                self.skipped += 1
                                continue

    def report(self):
        print(f"保存完成，共保存 {self.count} 条记录 -> {self.output_file}")
        print(f"跳过的记录数: {self.skipped}")
        print("字段统计：", self.keys)


def main():
    parser = argparse.ArgumentParser(description="清洗中文维基百科文本，转换为简体并保存为 JSONL 格式")
    parser.add_argument('--input_dir', type=str, default='extracted', help='输入目录（包含 WikiExtractor 输出子目录）')
    parser.add_argument('--output_file', type=str, default='cleaned_wiki_1000.jsonl', help='输出文件路径')
    parser.add_argument('--max_docs', type=int, default=1000, help='最多输出的文档数量（设为 -1 表示全部）')
    parser.add_argument('--min_length', type=int, default=100, help='保留文本最小长度（默认100字符）')
    args = parser.parse_args()

    cleaner = WikiCleaner(
        input_dir=args.input_dir,
        output_file=args.output_file,
        max_docs=args.max_docs,
        min_length=args.min_length,
    )
    cleaner.process()
    cleaner.report()


if __name__ == "__main__":
    main()
