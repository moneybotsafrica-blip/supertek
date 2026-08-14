# Mustek East Africa E-commerce Website

Mustek East Africa is a Django-based e-commerce website designed as a supplier of outdoor and camping equipment in Kenya. The website provides a modern and user-friendly shopping experience for customers looking to purchase high-quality outdoor products.

## Features

- **Responsive Design**: Mobile-friendly interface that works seamlessly across different device sizes
- **Product Catalog**: Organized by categories including outdoor equipment, camping gear, and accessories
- **Shopping Cart**: Add, update and remove products from cart with AJAX functionality
- **Checkout Process**: Simple and intuitive checkout flow
- **Order Management**: Track and manage orders through the admin panel
- **Admin Dashboard**: Comprehensive admin interface for product and order management

## Technology Stack

- **Backend**: Django 5.x
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite (default), can be configured for PostgreSQL
- **Image Handling**: Pillow

## Installation and Setup

1. **Clone the repository**:
   ```
   git clone https://github.com/yourusername/mustekea.git
   cd mustekea
   ```

2. **Create and activate a virtual environment**:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```
   python manage.py migrate
   ```

5. **Create a superuser**:
   ```
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```
   python manage.py runserver
   ```

7. **Visit the site in your browser**:
   - Main website: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Setting Up Product Categories and Products

1. Log in to the admin panel with your superuser credentials
2. Create parent categories (e.g., Camping Equipment, BBQ & Grilling)
3. Create subcategories under parent categories
4. Add products with appropriate categories, prices, and details
5. Upload product images using the inline product image editor

## Custom Settings

You can customize the following settings in `settings.py`:

- `MEDIA_ROOT`: Where uploaded product images are stored
- `STATIC_ROOT`: Where static files are collected for deployment

## Deployment

For production deployment:

1. Set `DEBUG = False` in settings.py
2. Configure a production-ready database (PostgreSQL recommended)
3. Set up proper static file serving with a web server like Nginx
4. Use a WSGI server like Gunicorn to serve the application

## License

This project is proprietary and intended for use by Mustek East Africa only.

## Contact

For questions or support regarding this project, please contact:
- Email: info@mustekea.co.ke
- Phone: +254 700 000000 