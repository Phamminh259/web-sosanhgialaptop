from datetime import datetime, timedelta
from email.mime.text import MIMEText
import base64
import io
import pandas as pd
import matplotlib.pyplot as plt
import re
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
from flask import (Flask, render_template, request, jsonify, redirect, url_for, flash, session)
from flask_session import Session
from google.auth.transport import requests
from google.oauth2 import id_token
from werkzeug.security import check_password_hash
from sqlalchemy import create_engine, func, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from database import Product, PriceHistory, Notification, Account , SessionLocal 
from werkzeug.security import check_password_hash, generate_password_hash


import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)
app.secret_key = 'minh123'

# Kết nối đến cơ sở dữ liệu
DATABASE_URL = "postgresql://minhminh:2003@localhost/Datass"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
db_session = Session()


@app.route('/')
def home():
    return render_template('home.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Truy xuất từ cơ sở dữ liệu bảng account
        account = db_session.query(Account).filter_by(email=email, password=password).first()
        
        if account:
            session['username'] = account.username  # Lưu username vào session
            flash(f"Đăng nhập thành công! Xin chào {account.username}")
            return redirect(url_for('home'))
        else:
            error_message = "Email hoặc mật khẩu không đúng. Vui lòng thử lại."
            return render_template('login.html', error=error_message)

    return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Kiểm tra xem email đã tồn tại chưa
        existing_account = db_session.query(Account).filter_by(email=email).first()
        
        if existing_account:
            error_message = "Email đã được sử dụng. Vui lòng chọn email khác."
            return render_template('register.html', error=error_message)
        
        # Thêm tài khoản mới vào cơ sở dữ liệu với role là "User"
        new_account = Account(username=username, email=email, password=password, role='User')
        db_session.add(new_account)
        db_session.commit()
        
        flash("Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.")
        return redirect(url_for('login'))

    return render_template('register.html')
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Đăng xuất thành công!")
    return redirect(url_for('home'))



@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()

    # Tạo một phiên mới cho mỗi yêu cầu
    db_session = Session()

    # Nếu ô tìm kiếm trống, lấy tất cả sản phẩm
    if not query:
        products = db_session.query(Product).all()
    else:
        # Thực hiện tìm kiếm theo từ khóa
        products = db_session.query(Product).filter(Product.product_name.ilike(f'%{query}%')).all()
    
    return render_template('search_results.html', products=products)  # Trang kết quả tìm kiếm
@app.route('/filter_products', methods=['GET'])
def filter_products():
    sort_order = request.args.get('sort')
    website = request.args.get('website')
    
    # Lọc và sắp xếp sản phẩm từ cơ sở dữ liệu
    products = get_filtered_products(sort_order=sort_order, website=website)

    # Render lại các sản phẩm đã được lọc/sắp xếp vào HTML
    return render_template('product_list.html', products=products)


def get_filtered_products(sort_order=None, website=None):
    query = db_session.query(Product)
    if website:
        query = query.filter(Product.website == website)
    if sort_order == 'asc':
        query = query.order_by(Product.current_price.asc())
    elif sort_order == 'desc':
        query = query.order_by(Product.current_price.desc())
    products = query.all()
    return products

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.close()











@app.route('/compare_prices')
def compare_prices():
    # Lấy danh sách ID sản phẩm từ tham số URL
    ids = request.args.get('ids')
    if ids:
        product_ids = ids.split(',')
        products = get_products_by_ids(product_ids)  # Hàm này cần được định nghĩa
    else:
        products = []

    return render_template('compare_prices.html', products=products)


@app.template_filter('format_price')
def format_price(price):
    if price is not None:
        return f"{price:,.0f} đ"  # Định dạng số với dấu phẩy và thêm "đ" ở cuối
    return "N/A"  # Trả về "N/A" nếu giá là None



@app.route('/compare/<int:product_id>')
def compare(product_id):
    # Tạo một phiên mới cho mỗi yêu cầu
    db_session = Session()

    # Lấy sản phẩm từ ID
    product = db_session.query(Product).filter_by(id=product_id).first()

    if not product:
        return "<h2>No product found with the given ID.</h2>"
    
    # Trích phần chính của tên sản phẩm
    main_name_part = " ".join(product.product_name.split()[:4])  # Lấy 4 từ đầu của tên sản phẩm

    # Tìm các sản phẩm khác có tên tương tự nhưng không trùng website
    products = db_session.query(Product).filter(
        Product.product_name.ilike(f'%{main_name_part}%'),
        Product.website != product.website  # Không lấy cùng website
    ).distinct(Product.website).all()  # Lấy mỗi website 1 lần duy nhất

    if not products:
        return "<h2>No products found for comparison.</h2>"

    # Thêm sản phẩm chính vào danh sách so sánh
    products.insert(0, product)

    # Render ra giao diện so sánh
    return render_template('compare.html', products=products, product_name=product.product_name)

@app.route('/submit_notification', methods=['POST'])
def submit_notification():
    email = request.form['email']
    product_id = request.form['product_id']  # Lấy product_id từ form

    if product_id is None or email is None:
        return "Product ID and email are required", 400

    # Tạo thông báo mới
    notification = Notification(email=email, product_id=product_id, is_sent=False, created_at=datetime.now())
    
    # Lưu thông báo vào cơ sở dữ liệu
    db_session.add(notification)
    db_session.commit()

    return "Notification submitted", 200

@app.route('/product_detail/<int:product_id>', methods=['GET'])
def product_detail(product_id):
    # Lấy sản phẩm từ ID
    product = db_session.query(Product).filter_by(id=product_id).first()
    
    if not product:
        return "<h2>No product found with the given ID.</h2>"
    
    # Render template chi tiết sản phẩm và truyền thông tin sản phẩm
    return render_template('product_detail.html', product=product)








# Route trang admin
@app.route('/admin', methods=['GET'])
def admin():
    if 'admin_logged_in' not in session:
        flash('Bạn cần đăng nhập để truy cập trang này!', 'danger')
        return redirect(url_for('admin_login'))

    # Kiểm tra tài khoản admin
    db_session = SessionLocal()
    admin_account = db_session.query(Account).filter(Account.email == session['admin_email']).first()

    if not admin_account or admin_account.role != 'Admin':
        flash('Bạn không có quyền truy cập vào trang này!', 'danger')
        db_session.close()
        return redirect(url_for('admin_login'))

    accounts = db_session.query(Account).all()
    notifications = db_session.query(Notification).all()
    db_session.close()

    return render_template('admin.html', accounts=accounts, notifications=notifications)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email'].strip()  # Bỏ khoảng trắng
        password = request.form['password'].strip()  # Bỏ khoảng trắng
        
        # Kiểm tra tài khoản admin
        db_session = SessionLocal()
        admin_account = db_session.query(Account).filter(Account.email == email).first()
        
        # Kiểm tra xem admin_account có tồn tại và mật khẩu có khớp không
        if admin_account:
            if admin_account.password == password:  # So sánh mật khẩu trực tiếp
                # Kiểm tra xem tài khoản có phải là admin không
                if admin_account.role == 'Admin':
                    session['admin_logged_in'] = True
                    session['admin_email'] = email
                    flash('Đăng nhập thành công!', 'success')
                    return redirect(url_for('admin'))
                else:
                    flash('Bạn không phải là tài khoản admin!', 'danger')
            else:
                flash('Email hoặc mật khẩu không đúng!', 'danger')  # Sai mật khẩu
        else:
            flash('Email hoặc mật khẩu không đúng!', 'danger')  # Sai email

        db_session.close()
    
    return render_template('admin_login.html')  # Tạo trang đăng nhập admin riêng


@app.route('/admin/accounts/add', methods=['POST'])
def add_account():
    email = request.form['email']
    password = request.form['password']
    username = request.form['username']
    role = request.form['role']

    db_session = SessionLocal()
    new_account = Account(email=email, password=generate_password_hash(password), username=username, role=role)
    db_session.add(new_account)
    db_session.commit()
    db_session.close()

    flash('Tài khoản đã được thêm!', 'success')
    return redirect(url_for('admin'))

# Route để sửa tài khoản
@app.route('/admin/accounts/edit/<int:id>', methods=['GET', 'POST'])
def edit_account(id):
    db_session = SessionLocal()

    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        role = request.form['role']

        account = db_session.query(Account).filter(Account.id == id).first()
        if account:
            account.email = email
            account.username = username
            account.role = role
            db_session.commit()
            flash('Tài khoản đã được cập nhật!', 'success')
        else:
            flash('Không tìm thấy tài khoản!', 'danger')

        db_session.close()
        return redirect(url_for('admin'))

    account = db_session.query(Account).filter(Account.id == id).first()
    db_session.close()
    return render_template('edit_account.html', account=account)

# Route để xóa tài khoản
@app.route('/admin/accounts/delete/<int:id>', methods=['POST'])
def delete_account(id):
    db_session = SessionLocal()
    account = db_session.query(Account).filter(Account.id == id).first()

    if account:
        db_session.delete(account)
        db_session.commit()
        flash('Tài khoản đã được xóa!', 'success')
    else:
        flash('Không tìm thấy tài khoản!', 'danger')

    db_session.close()
    return redirect(url_for('admin'))

# Route để thêm thông báo
@app.route('/admin/notifications/add', methods=['POST'])
def add_notification():
    email = request.form['email']
    product_id = request.form['product_id']

    db_session = SessionLocal()
    new_notification = Notification(email=email, product_id=product_id)
    db_session.add(new_notification)
    db_session.commit()
    db_session.close()

    flash('Thông báo đã được thêm!', 'success')
    return redirect(url_for('admin'))

# Route để xóa thông báo
@app.route('/admin/notifications/delete/<int:id>', methods=['POST'])
def delete_notification(id):
    db_session = SessionLocal()
    notification = db_session.query(Notification).filter(Notification.id == id).first()

    if notification:
        db_session.delete(notification)
        db_session.commit()
        flash('Thông báo đã được xóa!', 'success')
    else:
        flash('Không tìm thấy thông báo!', 'danger')

    db_session.close()
    return redirect(url_for('admin'))





@app.route('/price_history/<int:product_id>', methods=['GET'])
def price_history(product_id):
    # Tạo một phiên mới cho mỗi yêu cầu
    db_session = Session()

    # Lấy số ngày từ tham số query, mặc định là 30 nếu không có
    days = request.args.get('days', default=30, type=int)

    # Lấy dữ liệu lịch sử giá trong số ngày xác định
    history = db_session.query(PriceHistory).filter(
        PriceHistory.product_id == product_id,
        PriceHistory.crawl_time >= (datetime.now() - timedelta(days=days))
    ).order_by(PriceHistory.crawl_time).all()

    # Kiểm tra xem có dữ liệu không
    if not history:
        return "<h2>No price history data available for this product.</h2>"

    # Chuyển dữ liệu thành DataFrame để xử lý
    df = pd.DataFrame([(h.crawl_time, h.price_at_crawl) for h in history], columns=['crawl_time', 'price_at_crawl'])

    # Chuyển crawl_time thành chỉ ngày (bỏ giờ)
    df['crawl_date'] = df['crawl_time'].dt.date

    # Nhóm theo ngày và lấy giá trị cuối cùng trong ngày
    df_grouped = df.groupby('crawl_date').agg({'price_at_crawl': 'last'}).reset_index()

    # Chỉ lấy 5 ngày gần nhất (sắp xếp theo ngày giảm dần và lấy 5 dòng đầu tiên)
    df_grouped = df_grouped.sort_values(by='crawl_date', ascending=False).head(5)

    # Sắp xếp lại theo thứ tự tăng dần để vẽ biểu đồ
    df_grouped = df_grouped.sort_values(by='crawl_date')

    # Chuẩn bị dữ liệu cho biểu đồ
    dates = df_grouped['crawl_date']
    prices = df_grouped['price_at_crawl']

    # Vẽ biểu đồ bằng matplotlib
    plt.figure(figsize=(10, 5))
    plt.plot(dates, prices, marker='o')

    # Định dạng trục X để chỉ hiển thị ngày
    plt.gca().set_xticks(dates)
    plt.gca().set_xticklabels([date.strftime('%d/%m/%Y') for date in dates])

    # Định dạng trục Y (giá) với dấu phẩy và định dạng như 14.390.000
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x):,}'.replace(",", ".")))

    # Thêm tiêu đề và nhãn
    plt.title('Biểu đồ biến động giá sản phẩm')
    plt.xlabel('Ngày')
    plt.ylabel('Giá (VND)')
    plt.grid(True)

    # Chuyển biểu đồ thành image URL
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()  # Đảm bảo đóng biểu đồ sau khi lưu

    # Render template và truyền plot_url
    return render_template('price_history.html', plot_url=f"data:image/png;base64,{plot_url}", product_id=product_id)



# tab in icon
@app.route('/price_history_multi', methods=['GET'])
def price_history_multi():
    # Lấy danh sách ID sản phẩm từ query string
    product_ids = request.args.get('product_ids', '')
    product_ids = product_ids.split(',')

    # Kiểm tra xem có ID sản phẩm nào không
    if not product_ids:
        return "<h2>Không có sản phẩm nào để hiển thị lịch sử giá.</h2>"

    # Tạo một phiên cơ sở dữ liệu (giả sử bạn đã cấu hình SQLAlchemy)
    db_session = Session()

    # Biến lưu trữ dữ liệu lịch sử giá cho tất cả sản phẩm
    all_price_histories = []

    # Lặp qua từng ID sản phẩm để lấy dữ liệu lịch sử giá
    for product_id in product_ids:
        history = db_session.query(PriceHistory).filter(
            PriceHistory.product_id == product_id,
            PriceHistory.crawl_time >= (datetime.now() - timedelta(days=30))
        ).order_by(PriceHistory.crawl_time).all()

        # Chuyển dữ liệu thành DataFrame để xử lý
        df = pd.DataFrame(
            [(h.crawl_time, h.price_at_crawl) for h in history],
            columns=['crawl_time', 'price_at_crawl']
        )

        # Chuyển đổi crawl_time thành chỉ ngày
        if not df.empty:
            df['crawl_date'] = df['crawl_time'].dt.date
            df_grouped = df.groupby('crawl_date').agg({'price_at_crawl': 'last'}).reset_index()
            df_grouped = df_grouped.sort_values(by='crawl_date')
            all_price_histories.append((product_id, df_grouped))

    # Vẽ biểu đồ nếu có dữ liệu
    if not all_price_histories:
        return "<h2>Không có dữ liệu lịch sử giá để hiển thị.</h2>"

    plt.figure(figsize=(12, 6))
    for product_id, df_grouped in all_price_histories:
        plt.plot(df_grouped['crawl_date'], df_grouped['price_at_crawl'], marker='o', label=f"Sản phẩm {product_id}")

    plt.title('Biểu đồ biến động giá sản phẩm')
    plt.xlabel('Ngày')
    plt.ylabel('Giá (VND)')

    # Định dạng cột giá để hiển thị dấu chấm
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x):,}'.replace(",", ".")))

    plt.legend()
    plt.grid(True)

    # Chuyển biểu đồ thành image URL
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    # Đóng phiên cơ sở dữ liệu
    db_session.close()

    # Render template với biểu đồ
    return render_template('price_history_multi.html', plot_url=f"data:image/png;base64,{plot_url}")




if __name__ == '__main__':
    app.run(debug=True)

