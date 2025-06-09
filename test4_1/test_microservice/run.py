from parser_service.parse_app import app

if __name__ == "__main__":
    # category = 'SALE > Shop Deals > Hat Sale'
    # parser_script(category)
    app.run(host="0.0.0.0", port=5000, debug=True)