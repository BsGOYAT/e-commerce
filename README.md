# Aapki Dukan - E-commerce Website

A modern e-commerce website built with Python Flask, featuring a clean black, white, and grey theme similar to Amazon.

## Features

- Modern and responsive design
- Product listing and details
- Shopping cart functionality
- User authentication
- Clean and intuitive interface

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Project Structure

- `app.py` - Main application file
- `templates/` - HTML templates
  - `base.html` - Base template with common layout
  - `index.html` - Home page with product listings
  - `cart.html` - Shopping cart page
- `requirements.txt` - Python dependencies

## Customization

You can customize the website by:
1. Modifying the CSS variables in `base.html`
2. Adding more products to the database
3. Customizing the templates in the `templates/` directory

## License

This project is open source and available under the MIT License.