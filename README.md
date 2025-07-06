# Wiki-Media-Prepare

本项目用于中文维基百科数据的预处理，包括从原始 `XML dump` 到清洗后的简体中文 `JSONL` 格式文本的转换，适用于下游大语言模型预训练。

---

## 数据获取

由于题目中给出的数据链接（`https://dumps.wikimedia.org/zhwiki/20250201/`）已失效，我们改用最新版本：

- 数据来源：[https://dumps.wikimedia.org/zhwiki/20250701/](https://dumps.wikimedia.org/zhwiki/20250701/)
- 文件名称：`zhwiki-20250701-pages-articles-multistream.xml.bz2`

```bash
wget https://dumps.wikimedia.org/zhwiki/20250701/zhwiki-20250701-pages-articles-multistream.xml.bz2
```

---

## 环境依赖

使用`conda`管理环境，并安装以下依赖：

```bash
conda create --name wikimedia python=3.10 -y
conda activate wikimedia
pip install -r requirements.txt
```
**请确保`python`版本最高为`3.10`！**

---

## 使用方法

### 1. 提取原始文本

使用 [WikiExtractor](https://github.com/attardi/wikiextractor) 提取 `Wikipedia` 原始内容：

```bash
chmod -x ./extract.sh 
./extract.sh
```

其中 `extract.sh` 内容如下：

```bash
#!/bin/bash
python -m wikiextractor.WikiExtractor \
   -b 10M \
   -o extracted \
   --json \
   --no-templates \
   zhwiki-20250701-pages-articles-multistream.xml.bz2
```

提取结果将被保存在 `extracted/` 目录下，结构为分段的子目录（如 `AA/wiki\_00`、`AB/wiki\_01` ...）。

---

### 2. 清洗维基内容

使用 `wiki2json.py` 对提取结果进行进一步清洗：

```bash
python wiki2json.py \
  --input_dir extracted \
  --output_file cleaned_wiki_1000.jsonl \
  --max_docs 1000 \
  --min_length 100
```

清洗后将输出为 `JSONL` 格式，形如：

```json

{
    "text": "高加索犹太人，或称“山区犹太人”，……", 
    "meta": {
        "id": "1292666", 
        "revid": "1334784", 
        "url": "https://zh.wikipedia.org/wiki/高加索犹太人", 
        "title": "高加索犹太人"
        }
}
```

---

## 清洗策略说明

- 使用 `mwparserfromhell` 移除维基语法与模板；
- 使用 `OpenCC` 将内容统一转换为简体中文（t2s）；
- 过滤非主命名空间的页面（如“分类:”、“模板:”等）；
- 去除文本长度不足 100 字的页面；
- 所有页面元数据（除正文 `text` 外）均存储于 `"meta"` 字段中，便于下游使用。

## 遇到的问题及解决方案

| 问题           | 描述                    | 解决方案                    |                             |
| ------------ | --------------------- | ----------------------- | --------------------------- |
| 部分页面为分类页/重定向 | 非主内容                  | 直接跳过                    |                             |
| Wiki 语法嵌套复杂  | \`\[\[链接              \| 显示文本]]\` 等多层嵌套          | 使用 `mwparserfromhell` 做标准解析 |
| 繁简体混杂        | 预训练需统一语言规范            | 通过 `OpenCC` 进行简繁转换      |                             |
| 特殊字符         | 多余换行、不可见符号等           | 标准清洗合并空格、剥离不可见字符        |                             |

---


## 输出说明

最终输出为 `JSON` `Lines` 格式，每行一个文档：

- `text` 字段：清洗后正文内容
- `meta` 字段：页面元数据（标题、`URL`、`ID` 等）

---

## 可选参数说明

| 参数名             | 说明                         | 示例值                  |
| --------------- | -------------------------- | -------------------- |
| `--input_dir`   | 输入目录（`WikiExtractor` 输出目录）   | `extracted`          |
| `--output_file` | 输出 `JSONL` 路径                | `cleaned_wiki.jsonl` |
| `--max_docs`    | 最大输出文档数（默认 1000，设为 -1 则不限） | `1000`               |
| `--min_length`  | 最小正文长度（字符）                 | `100`                |
