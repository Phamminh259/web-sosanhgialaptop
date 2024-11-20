from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey,Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import psycopg2

# Kết nối tới PostgreSQL
DATABASE_URL = "postgresql://minhminh:2003@localhost/Datass"
engine = create_engine(DATABASE_URL)

# Khởi tạo cơ sở dữ liệu
Base = declarative_base()

# Tạo session để tương tác với cơ sở dữ liệu
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# Định nghĩa bảng Product cho từng sản phẩm crawl được
class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    original_price = Column(Float)
    description = Column(String)
    img = Column(String)
    website = Column(String, nullable=False)  # Nguồn từ trang web nào

    # Mối quan hệ với bảng PriceHistory
    price_histories = relationship('PriceHistory', back_populates='product')

# Định nghĩa bảng PriceHistory để lưu lịch sử giá
class PriceHistory(Base):
    __tablename__ = 'price_histories'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    crawl_time = Column(DateTime(timezone=True), server_default=func.now())
    price_at_crawl = Column(Float, nullable=False)

    # Mối quan hệ với bảng Product
    product = relationship('Product', back_populates='price_histories')
    
class Notification(Base):
    __tablename__ = 'notifications'
    
    # Thêm khóa chính
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    email = Column(String, nullable=False)  # Email người nhận thông báo
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)  # Tham chiếu tới sản phẩm
    is_sent = Column(Boolean, default=False)  # Đã gửi email hay chưa
    created_at = Column(DateTime, default=datetime.utcnow)  # Add this line
    account_id = Column(Integer, nullable=True)
    
class Account(Base):
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Ví dụ: 'User' hoặc 'Admin'
    username = Column(String, nullable=False)    

    

# Tạo các bảng trong cơ sở dữ liệu
Base.metadata.create_all(bind=engine)

def save_product(product_data):
    """
    Hàm lưu thông tin sản phẩm và lịch sử giá vào cơ sở dữ liệu.
    """
    product = session.query(Product).filter_by(product_name=product_data['product_name'], website=product_data['website']).first()
    
    # Nếu sản phẩm đã tồn tại, cập nhật lịch sử giá
    if product:
        price_history = PriceHistory(product_id=product.id, price_at_crawl=product_data['current_price'])
        session.add(price_history)
    else:
        # Nếu sản phẩm chưa tồn tại, thêm sản phẩm và lịch sử giá mới
        product = Product(
            product_name=product_data['product_name'],
            current_price=product_data['current_price'],
            original_price=product_data['original_price'],
            description=product_data['description'],
            img=product_data['img'],
            website=product_data['website']
        )
        session.add(product)
        session.flush()  # Đẩy dữ liệu để lấy product.id

        price_history = PriceHistory(product_id=product.id, price_at_crawl=product_data['current_price'])
        session.add(price_history)

    session.commit()

