import os
import fitz  # PyMuPDF
import re

# --- 设置根目录 ---
ROOT_DIR = "Sepsis_Papers"

def clean_text(text):
    """
    清洗文本：去重换行、去不换行空格
    """
    if not text: return ""
    text = text.replace(u'\xa0', ' ') 
    # 把换行符替换成空格，防止断句错误
    text = text.replace('\n', ' ') 
    # 把多个连续空格合并成一个
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def read_pdf(file_path):
    """
    使用 fitz (PyMuPDF) 读取 PDF
    """
    try:
        doc = fitz.open(file_path)
        full_text = []
        for page in doc:
            full_text.append(page.get_text())
        doc.close()
        return clean_text(" ".join(full_text))
    except Exception as e:
        print(f"   ❌ 读取失败: {os.path.basename(file_path)} -> {e}")
        return None

def main():
    if not os.path.exists(ROOT_DIR):
        print(f"❌ 错误：找不到根目录 '{ROOT_DIR}'")
        return

    all_data = {} # 存储所有结果 { "分类/文件名": 内容 }
    
    print(f"🚀 开始扫描 '{ROOT_DIR}' 下的所有文件...")
    print("-" * 60)

    # os.walk 会像爬虫一样钻进每一个子文件夹
    for root, dirs, files in os.walk(ROOT_DIR):
        # 获取当前文件夹的名字（作为分类标签）
        category = os.path.basename(root)
        
        # 只处理 PDF
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        if pdf_files:
            print(f"\n📂 进入分类文件夹: 【{category}】 (发现 {len(pdf_files)} 篇)")
            
            for f in pdf_files:
                full_path = os.path.join(root, f)
                print(f"   📄 读取: {f} ... ", end="")
                
                content = read_pdf(full_path)
                
                if content and len(content) > 500:
                    # 记录 Key 为 "分类/文件名"，防止不同文件夹有同名文件冲突
                    key = f"{category}/{f}"
                    all_data[key] = content
                    print(f"✅ (字数: {len(content)})")
                else:
                    print("⚠️ (内容无效或过短)")
        else:
            # 如果是空文件夹或只有根目录，跳过打印
            pass

    print("-" * 60)
    print(f"🎉 全部处理完毕！共读取 {len(all_data)} 篇有效论文。")
    
    # 打印一下找到了哪些分类，确认是否都读到了
    categories_found = set(k.split('/')[0] for k in all_data.keys())
    print(f"📊 包含的分类: {categories_found}")

if __name__ == "__main__":
    main()