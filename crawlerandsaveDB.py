import re
import requests
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey,Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from bs4 import BeautifulSoup
from sqlalchemy.sql import func
from datetime import datetime
import json
# Khai báo cơ sở dữ liệu
Base = declarative_base()

# Định nghĩa bảng Product
class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    product_name = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    original_price = Column(Float)
    description = Column(String)
    img = Column(String)
    website = Column(String, nullable=False)  # Nguồn từ trang web nào
    price_histories = relationship('PriceHistory', back_populates='product')
# class Product(Base):
#     __tablename__ = 'products'
    
#     id = Column(Integer, primary_key=True)
#     product_name = Column(String, nullable=False)
#     current_price = Column(Float, nullable=False)
#     original_price = Column(Float)
#     description = Column(String)
#     img = Column(String)
#     website = Column(String, nullable=False)  # Nguồn từ trang web nào
#     last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # Thời gian cập nhật cuối cùng
#     price_histories = relationship('PriceHistory', back_populates='product')


# Định nghĩa bảng PriceHistory để lưu lịch sử giá
class PriceHistory(Base):
    __tablename__ = 'price_histories'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    crawl_time = Column(DateTime(timezone=True), server_default=func.now())
    price_at_crawl = Column(Float, nullable=False)
    product = relationship('Product', back_populates='price_histories')
    
class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)  # Khóa chính
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    email = Column(String, nullable=False)  # Email của người dùng
    is_sent = Column(Boolean, default=False)  # Đã gửi email hay chưa
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Thời gian tạo
    product = relationship('Product')  # Quan hệ với bảng products



# # Chuyển đổi chuỗi giá thành định dạng float
# def convert_price(price_str):
#     if price_str:
#         number = float(price_str.replace('.', '').replace(',', '').replace('₫', '').replace('đ', '').strip())
#         return number
#     return None 
# def convert_price(price_str):
#     # Nếu price_str là None, hoặc không phải là chuỗi, trả về None
#     if price_str is None:
#         return None
    
#     # Nếu price_str không phải là chuỗi, trả về giá trị hiện tại
#     if isinstance(price_str, float) or isinstance(price_str, int):
#         return float(price_str)

#     # Nếu là chuỗi, kiểm tra xem nó có rỗng không
#     if isinstance(price_str, str):
#         price_str = price_str.strip()  # Xóa khoảng trắng
#         if not price_str:  # Nếu chuỗi rỗng
#             return 0.0  # Hoặc trả về giá trị mặc định khác như None

#         # Thực hiện các thao tác thay thế ký tự
#         return float(price_str.replace('.', '').replace(',', '').replace('₫', '').replace('đ', '').strip())
    
#     # Nếu không thuộc các trường hợp trên, trả về None
#     return None

# def convert_price(price_str):
#     # Nếu price_str là None, hoặc không phải là chuỗi, trả về None
#     if price_str is None:
#         return None
    
#     # Nếu price_str không phải là chuỗi, trả về giá trị hiện tại
#     if isinstance(price_str, float) or isinstance(price_str, int):
#         return float(price_str)

#     # Nếu là chuỗi, kiểm tra xem nó có rỗng hoặc không hợp lệ không
#     if isinstance(price_str, str):
#         price_str = price_str.strip()  # Xóa khoảng trắng
#         if not price_str or price_str in ['Liên hệ', 'Không có giá', 'Giá liên hệ']:  # Thêm các giá trị không hợp lệ khác nếu cần
#             return 0.0  # Hoặc trả về giá trị mặc định khác như None

#         # Thực hiện các thao tác thay thế ký tự
#         return float(price_str.replace('.', '').replace(',', '').replace('₫', '').replace('đ', '').strip())
    
#     # Nếu không thuộc các trường hợp trên, trả về None
#     return None
def convert_price(price_str):
    # Nếu price_str là None, hoặc không phải là chuỗi, trả về None
    if price_str is None:
        return None
    
    # Nếu price_str là số, chuyển đổi trực tiếp thành float
    if isinstance(price_str, (float, int)):
        return float(price_str)

    # Nếu là chuỗi, kiểm tra xem nó có rỗng hoặc không hợp lệ không
    if isinstance(price_str, str):
        price_str = price_str.strip()  # Xóa khoảng trắng thừa
        # Kiểm tra các giá trị không hợp lệ
        if price_str in ['Liên hệ', 'Không có giá', 'Giá liên hệ']:  # Thêm các giá trị không hợp lệ khác nếu cần
            return 0.0  # Trả về 0.0 thay vì None cho các trường hợp này

        # Thực hiện các thao tác thay thế ký tự và chuyển đổi giá
        try:
            return float(price_str.replace('.', '').replace(',', '').replace('₫', '').replace('đ', '').strip())
        except ValueError:
            return 0.0  # Trả về 0.0 nếu chuyển đổi thất bại

    # Nếu không thuộc các trường hợp trên, trả về None
    return None





# Hàm crawl dữ liệu từ tinhocngoisao
def crawl_website_tinhocngoisao(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    products = []
    product_elements = soup.find_all('div', class_='product-item')
    for product_element in product_elements:
        product_name = product_element.find('a', class_='productName product-link').text.strip()
        current_price_element = product_element.find('p', class_='pdPrice').find('span').text.strip()
        original_price_element = product_element.find('p', class_='pdPrice').find('del')
        
        if original_price_element:
            original_price_element = original_price_element.text.strip()
        else:
            original_price_element = current_price_element
        
        pictures = product_element.find('picture').find('img').get('data-src')
        
        description_elements_temp = product_element.find_all('div', class_='taginforitemflex')
        description_elements = ''.join(item.find('span').text.strip() for item in description_elements_temp)
   
        products.append({
            'product_name': product_name,
            'current_price': current_price_element,
            'original_price': original_price_element,
            'description': description_elements,
            'img': 'http:' + pictures,
            'website': 'tinhocngoisao'
        })

    return products

# Hàm crawl dữ liệu từ laptop88
def crawl_website_laptop_88(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    products = []
    product_elements = soup.find_all('div', class_='product-item')

    for product_element in product_elements:
        product_name = product_element.find('h2', class_='product-title').find('a').text.strip()
        current_price_element = product_element.find('div', class_='price-bottom').find('span').text.strip()
        
        original_price_element = product_element.find('div', class_='price-top d-flex align-items text-center space-center').find('del', class_='old-price')
        if original_price_element:
            original_price_element = original_price_element.text.strip()
        else:
            original_price_element = current_price_element
        
        pictures = product_element.find('div', class_='product-img').find('img').get('src')
        
        description_elements_temp = product_element.find_all('tr')
        description_elements = ''
        for item in description_elements_temp:
            temp = item.find_all('td')
            for item1 in temp:
                if item1.find('p'):
                    description_elements += item1.find('p').text.strip()
                else:
                    description_elements += item1.text.strip()
                
        products.append({
            'product_name': product_name,
            'current_price': current_price_element,
            'original_price': original_price_element,
            'description': description_elements,
            'img': 'https://laptop88.vn/' + pictures,
            'website': 'laptop88'
        })

    return products

# Hàm crawl dữ liệu từ minhvu
def crawl_website_minhvu(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    products = []
    product_elements = soup.find_all('div', class_='col-md-2 col-sm-4 col-xs-6 row-sp')
    
    for product_element in product_elements:
        product_name = product_element.find('a', class_='ahover text-xanhla').text.strip()
        current_price_element = product_element.find('span', class_='text-giamoi').text.strip()
        if current_price_element == 'Liên hệ':
            continue
        
        original_price_element = product_element.find('span', class_='text-giacu')
        if original_price_element:
            original_price_element = original_price_element.text.strip()
        else:
            original_price_element = current_price_element

        pictures = product_element.find('img', class_='img-responsive').get('src')
        
        description_elements = product_element.find('p', class_='pro-desc').text.strip()
        
        products.append({
            'product_name': product_name,
            'current_price': current_price_element,
            'original_price': original_price_element,
            'description': description_elements,
            'img': 'https://minhvu.vn/' + pictures,
            'website': 'minhvu'
        })

    return products


    
# # Hàm crawl dữ liệu từ anphat
# def crawl_website_anphat(url):
#     headers = {'User-Agent': 'Mozilla/5.0'}
#     response = requests.get(url, headers=headers, timeout=10)
#     soup = BeautifulSoup(response.text, 'html.parser')
#     # print(soup)
#     products = []
#     product_elements = soup.find_all('div',class_='p-item')
   
#     for product_element in product_elements:
#         product_name = product_element.find('a', class_='p-name').text.strip()
#         current_price_element = product_element.find('span', class_='p-price').text.strip()
#         # if current_price_element == 'Liên hệ':
#         #     continue
        
#         original_price_element = product_element.find('del', class_='p-old-price')
#         if original_price_element:
#             original_price_element = original_price_element.text.strip()
#         else:
#             original_price_element = current_price_element

#         pictures = product_element.find('img').get('data-src')
        
#         description= product_element.find('div',class_='tooltip-summary').find_all('span', class_='item d-block')
#         description_elements=''
#         for item in description:
#             description_elements+= item.text.strip()
#             # print(description_elements)
#         products.append({
#             'product_name': product_name,
#             'current_price': current_price_element,
#             'original_price': original_price_element,
#             'description': description_elements,
#             'img': '' + pictures,
#             'website': 'anphat'
#         })

#     return products



def crawl_website_anphat(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    products = []
    product_elements = soup.find_all('div', class_='p-item')

    for product_element in product_elements:
        # Tên sản phẩm
        product_name_element = product_element.find('a', class_='p-name')
        product_name = product_name_element.text.strip() if product_name_element else 'No name'

        # Giá hiện tại
        current_price_element = product_element.find('span', class_='p-price')
        current_price = current_price_element.text.strip() if current_price_element else 'No price'

        # Giá gốc (nếu có)
        original_price_element = product_element.find('del', class_='p-old-price')
        if original_price_element:
            original_price = original_price_element.text.strip()
        else:
            original_price = current_price  # Nếu không có giá gốc, sử dụng giá hiện tại

        # Hình ảnh
        picture_element = product_element.find('img')
        pictures = picture_element.get('data-src') if picture_element else 'No image'

        # Mô tả sản phẩm (kiểm tra tồn tại trước khi truy cập)
        description_container = product_element.find('div', class_='tooltip-summary')
        description_elements = ''
        
        if description_container:
            description = description_container.find_all('span', class_='item d-block')
            for item in description:
                description_elements += item.text.strip() + ' '
        else:
            description_elements = 'No description'  # Giá trị mặc định nếu không có mô tả

        # Thêm sản phẩm vào danh sách
        products.append({
            'product_name': product_name,
            'current_price': current_price,
            'original_price': original_price,
            'description': description_elements.strip(),
            'img': '' + pictures if pictures != 'No image' else pictures,
            'website': 'anphat'
        })

    return products

# Hàm lưu sản phẩm và lịch sử giá vào cơ sở dữ liệu
# def save_product_and_price(product_data):
#     # Kiểm tra xem sản phẩm đã tồn tại chưa
#     product = session.query(Product).filter_by(product_name=product_data['product_name'], website=product_data['website']).first()
    
#     if product:
#         # Sản phẩm đã tồn tại, cập nhật lịch sử giá
#         price_history = PriceHistory(product_id=product.id, price_at_crawl=product_data['current_price'])
#         session.add(price_history)
#     else:
#         # Sản phẩm chưa tồn tại, thêm sản phẩm và lịch sử giá mới
#         product = Product(
#             product_name=product_data['product_name'],
#             current_price=product_data['current_price'],
#             original_price=product_data['original_price'],
#             description=product_data['description'],
#             img=product_data['img'],
#             website=product_data['website']
#         )
#         session.add(product)
#         session.flush()  # Đẩy dữ liệu vào DB để lấy product.id
        
#         price_history = PriceHistory(product_id=product.id, price_at_crawl=product_data['current_price'])
#         session.add(price_history)

#     session.commit()

from datetime import datetime, timedelta
def save_product_and_price(product_data):
    # Kiểm tra xem sản phẩm đã tồn tại chưa
    product = session.query(Product).filter_by(product_name=product_data['product_name'], website=product_data['website']).first()
    
    if product:
        # Sản phẩm đã tồn tại
        # Cập nhật giá gốc và giá hiện tại nếu có thay đổi
        if product.original_price != product_data['original_price'] or product.current_price != product_data['current_price']:
            product.original_price = product_data['original_price']
            product.current_price = product_data['current_price']
            # Cập nhật thời gian last_updated
            product.last_updated = datetime.now()

    else:
        # Sản phẩm chưa tồn tại, thêm sản phẩm mới
        product = Product(
            product_name=product_data['product_name'],
            current_price=product_data['current_price'],
            original_price=product_data['original_price'],
            description=product_data['description'],
            img=product_data['img'],
            website=product_data['website']
        )
        session.add(product)
        session.flush()  # Đẩy dữ liệu vào DB để lấy product.id

    # Kiểm tra xem đã có bản ghi lịch sử giá trong vòng 1 ngày chưa
    last_crawl_time = datetime.now() - timedelta(days=1) 
    existing_price_history = session.query(PriceHistory).filter(
        PriceHistory.product_id == product.id,
        PriceHistory.crawl_time > last_crawl_time
    ).first()

    # Chỉ lưu lịch sử giá nếu chưa có bản ghi nào trong 1 ngày qua
    if not existing_price_history:
        price_history = PriceHistory(product_id=product.id, price_at_crawl=product_data['current_price'])
        session.add(price_history)

    # Commit để lưu thay đổi vào cơ sở dữ liệu
    session.commit()




if __name__ == '__main__':
    all_products = []

# Loop through pages 1 to 30
for i in range(1, 25):
    urlanphat = 'https://www.anphatpc.com.vn/may-tinh-xach-tay-laptop.html?page=' + str(i)
    all_products.extend(crawl_website_anphat(urlanphat))

# # Now all_products contains the data from page 1 to 30

#     # Lưu dữ liệu vào file JSON
#     with open('products_data.json', 'w', encoding='utf-8') as f:
#         json.dump(all_products, f, ensure_ascii=False, indent=4)

#     print("Dữ liệu đã được lưu vào 'products_data.json'.")
    
    
    
    
    
    
    # URL để crawl dữ liệu
    urltinhocngoisao = 'https://tinhocngoisao.com/collections/laptop-ban-chay'  
    all_products.extend(crawl_website_tinhocngoisao(urltinhocngoisao))
    
    
    
    pages = [1, 2, 3, 4, 5, 6, 7]
    for page in pages:
       
       
        urlLaptop88 = 'https://laptop88.vn/may-tinh-xach-tay.html?page=' + str(page)  
        all_products.extend(crawl_website_laptop_88(urlLaptop88))
        
        
   
    for i in range(1, 10):
        urlminhvu = 'https://minhvu.vn/laptop-moi/?page=' + str(i)  
        all_products.extend(crawl_website_minhvu(urlminhvu))

    # Kết nối với cơ sở dữ liệu
    engine = create_engine("postgresql://minhminh:2003@localhost/Datass")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Chuyển đổi giá và lưu sản phẩm vào cả hai bảng products và price_histories
    for product_data in all_products:
        product_data["current_price"] = convert_price(product_data["current_price"])
        product_data["original_price"] = convert_price(product_data["original_price"])

        try:
            save_product_and_price(product_data)
        except Exception as e:
            print(f"Đã xảy ra lỗi: {e}")
