import os
import subprocess
import pandas as pd
import re
# import pikepdf # Bỏ comment nếu bạn muốn dùng pikepdf

# Danh sách các đặc trưng chính chúng ta muốn từ pdfid.py
# Đây là các keyword mà pdfid.py tìm kiếm
PDFID_KEYWORDS = [
    '/Page', '/Encrypt', '/ObjStm', '/JS', '/JavaScript',
    '/AA', '/OpenAction', '/AcroForm', '/JBIG2Decode',
    '/RichMedia', '/Launch', '/EmbeddedFile', '/XFA',
    '/Colors > 2^24'
]

# Các đặc trưng cơ bản khác
OTHER_FEATURES = ['obj', 'endobj', 'stream', 'endstream', 'xref', 'trailer', 'startxref']

def parse_pdfid_output(pdfid_text_output):
    """
    Phân tích output dạng text từ pdfid.py để lấy số lượng các keyword.
    Output của pdfid.py có dạng:
    Keyword        Count
    /Page          12
    /JS            1
    ...
    """
    features = {}
    # Khởi tạo tất cả các features với giá trị 0
    for key in PDFID_KEYWORDS + OTHER_FEATURES:
        # Chuẩn hóa tên feature (loại bỏ ký tự đặc biệt, thay thế bằng underscore)
        feature_name = re.sub(r'[^a-zA-Z0-9_]', '', key.replace('/', '_').replace(' > ', '_gt_')).lstrip('_')
        features[feature_name] = 0

    lines = pdfid_text_output.strip().split('\n')
    for line in lines:
        # Bỏ qua các dòng header hoặc không chứa thông tin count
        if "PDF Header" in line or "Keyword" in line or "Count" in line or not line.strip():
            continue
        
        parts = line.split()
        if len(parts) >= 2:
            keyword = parts[0]
            try:
                count = int(parts[1])
                # Chuẩn hóa tên feature
                feature_name = re.sub(r'[^a-zA-Z0-9_]', '', keyword.replace('/', '_').replace(' > ', '_gt_')).lstrip('_')
                if feature_name in features: # Chỉ lấy những features đã định nghĩa
                     features[feature_name] = count
                elif keyword in features: # Dành cho các keyword không có /
                     features[keyword] = count

            except ValueError:
                # Đôi khi có thể có các dòng không phải là count (ví dụ: các dòng về entropy)
                pass
    return features

def extract_features_with_pdfid(pdf_path):
    """
    Chạy pdfid.py và phân tích output của nó.
    """
    try:
        # Đảm bảo pdfid.py có trong PATH hoặc cung cấp đường dẫn đầy đủ
        # Ví dụ: '/usr/local/bin/pdfid.py'
        process = subprocess.run(['pdfid.py', pdf_path], capture_output=True, text=True, check=False, timeout=30) # Thêm timeout
        if process.returncode != 0:
            print(f"pdfid error for {pdf_path}: {process.stderr}")
            # Trả về dict rỗng hoặc dict với giá trị mặc định nếu pdfid lỗi
            return {re.sub(r'[^a-zA-Z0-9_]', '', key.replace('/', '_').replace(' > ', '_gt_')).lstrip('_'): 0 for key in PDFID_KEYWORDS + OTHER_FEATURES}

        return parse_pdfid_output(process.stdout)
    except subprocess.TimeoutExpired:
        print(f"Timeout processing {pdf_path} with pdfid.")
        return {re.sub(r'[^a-zA-Z0-9_]', '', key.replace('/', '_').replace(' > ', '_gt_')).lstrip('_'): 0 for key in PDFID_KEYWORDS + OTHER_FEATURES}
    except Exception as e:
        print(f"Error running pdfid for {pdf_path}: {e}")
        return {re.sub(r'[^a-zA-Z0-9_]', '', key.replace('/', '_').replace(' > ', '_gt_')).lstrip('_'): 0 for key in PDFID_KEYWORDS + OTHER_FEATURES}

# (Tùy chọn) Hàm trích xuất features bằng pikepdf
# def extract_features_with_pikepdf(pdf_path):
#     features = {}
#     try:
#         with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
#             features['pikepdf_page_count'] = len(pdf.pages)
#             # Đếm số lượng đối tượng JavaScript
#             js_objects = 0
#             if hasattr(pdf.Root, '/Names') and hasattr(pdf.Root.Names, '/JavaScript') and hasattr(pdf.Root.Names.JavaScript, '/Names'):
#                 js_objects += len(pdf.Root.Names.JavaScript.Names)
            
#             # Tìm trong các Actions của tài liệu hoặc trang
#             def count_js_in_obj(obj):
#                 count = 0
#                 if hasattr(obj, '/S') and obj.S == '/JavaScript' and hasattr(obj, '/JS'):
#                     count += 1
#                 # Đệ quy tìm trong các actions lồng nhau (ví dụ trong /AA)
#                 if isinstance(obj, pikepdf.Dictionary):
#                     for key in obj:
#                         if isinstance(obj[key], pikepdf.Dictionary):
#                             count += count_js_in_obj(obj[key])
#                         elif isinstance(obj[key], pikepdf.Array):
#                             for item in obj[key]:
#                                 if isinstance(item, pikepdf.Dictionary):
#                                     count += count_js_in_obj(item)
#                 return count

#             if hasattr(pdf.Root, '/OpenAction'):
#                 js_objects += count_js_in_obj(pdf.Root.OpenAction)
            
#             for page in pdf.pages:
#                 if hasattr(page, '/AA'): # Additional Actions
#                     js_objects += count_js_in_obj(page.AA)
#             features['pikepdf_js_count'] = js_objects

#     except Exception as e:
#         print(f"Error processing {pdf_path} with pikepdf: {e}")
#         features['pikepdf_page_count'] = 0 # Giá trị mặc định khi lỗi
#         features['pikepdf_js_count'] = 0
#     return features

def process_pdf_file(file_path, label_name, label_value):
    """
    Xử lý một file PDF đơn.
    """
    # Trích xuất features bằng pdfid
    pdfid_features = extract_features_with_pdfid(file_path)
    
    # (Tùy chọn) Trích xuất features bằng pikepdf
    # pikepdf_features = extract_features_with_pikepdf(file_path)
    
    # Kết hợp các features
    # current_features = {**pdfid_features, **pikepdf_features} # Nếu dùng cả hai
    current_features = pdfid_features

    # Thêm các thông tin khác
    current_features['filepath'] = file_path # Giữ lại đường dẫn file để tham khảo
    current_features['filename'] = os.path.basename(file_path)
    try:
        current_features['filesize_kb'] = os.path.getsize(file_path) / 1024
    except OSError:
        current_features['filesize_kb'] = 0

    # Sử dụng tên nhãn làm nhãn chính
    current_features['label'] = label_name
    
    return current_features

def process_directory(directory_path, label_name, label_value, recursive=False):
    """
    Xử lý tất cả các file PDF trong một thư mục.
    """
    records = []
    file_count = 0
    print(f"Processing directory: {directory_path} with label: {label_name}")
    
    # Hàm xử lý đệ quy để đi qua các thư mục con
    def walk_dir(dir_path):
        nonlocal file_count
        
        for entry in os.scandir(dir_path):
            if entry.is_file() and entry.name.lower().endswith('.pdf'):
                file_path = entry.path
                records.append(process_pdf_file(file_path, label_name, label_value))
                file_count += 1
                if file_count % 100 == 0:
                    print(f"Processed {file_count} files with label {label_name}...")
            
            # Nếu recursive=True, xử lý các thư mục con
            elif entry.is_dir() and recursive:
                walk_dir(entry.path)
    
    # Bắt đầu quá trình duyệt
    walk_dir(directory_path)
    
    print(f"Finished processing {file_count} files with label {label_name}.")
    return records

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    BENIGN_DIR = '/home/remnux/Desktop/extraction/data/Benign'  # Điều chỉnh đường dẫn này cho đúng
    MALICIOUS_DIR = '/home/remnux/Desktop/extraction/data/Malicious' # Điều chỉnh đường dẫn này cho đúng
    OUTPUT_CSV = '/home/remnux/Desktop/extraction/output/pdf_features.csv' # File output

    # Tạo thư mục processed nếu chưa có
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    all_pdf_records = []

    # Xử lý file lành tính - không cần đệ quy vào thư mục con
    benign_records = process_directory(BENIGN_DIR, "benign", 0, recursive=False)
    all_pdf_records.extend(benign_records)

    # Xử lý file độc hại - cần đệ quy vào thư mục con
    malicious_records = process_directory(MALICIOUS_DIR, "malicious", 1, recursive=True)
    all_pdf_records.extend(malicious_records)

    # Tạo DataFrame
    df_features = pd.DataFrame(all_pdf_records)

    # Xử lý giá trị thiếu (NaN) - ví dụ, điền bằng 0
    # Điều này quan trọng vì các mô hình ML không xử lý được NaN
    df_features = df_features.fillna(0) 

    # Lưu DataFrame ra file CSV
    df_features.to_csv(OUTPUT_CSV, index=False)
    print(f"Feature extraction complete. Data saved to {OUTPUT_CSV}")
    print(f"Total records: {len(df_features)}")
    print("Columns in DataFrame:", df_features.columns.tolist())
    print("Sample of data (first 5 rows):")
    print(df_features.head())