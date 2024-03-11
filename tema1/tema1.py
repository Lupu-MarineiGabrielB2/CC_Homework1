import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# In-memory storage for shops
shops = {}


# Load shops from a JSON file
def load_shops():
    try:
        with open('shops.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Save shops to a JSON file
def save_shops():
    with open('shops.json', 'w') as f:
        json.dump(shops, f)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        print("Parsed query parameters:", query_params)

        if parsed_path.path == '/shops':
            # GET all shops
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(list(shops.values())).encode())
        elif parsed_path.path == '/shop':
            # GET a specific shop by ID
            if 'id' in query_params:
                shop_id = query_params['id'][0]
                print("Requested shop ID:", shop_id)
                if shop_id.isdigit():
                    # print("Converted shop ID to integer:", shop_id)
                    if shops.get(shop_id) is not None:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(shops[shop_id]).encode())
                        return
                    else:
                        self.send_response(404)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "Shop not found"}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))

            # Check if required fields are present in the request body
            required_fields = ['address', 'contact_info', 'revenue', 'name']
            if not all(field in post_data for field in required_fields):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing required fields"}).encode())
                return

            # Check data types of fields
            if not isinstance(post_data['address'], str) or \
                    not isinstance(post_data['contact_info'], str) or \
                    not isinstance(post_data['revenue'], (int, float)) or \
                    not isinstance(post_data['name'], str):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid data types"}).encode())
                return

            # Check if the resource already exists
            for shop_id, shop_data in shops.items():
                if shop_data['name'] == post_data['name']:
                    self.send_response(409)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Shop already exists"}).encode())
                    return
            # Generate a unique ID for the new shop
            shop_id = len(shops) + 1
            post_data['id'] = shop_id

            # Add the new shop to the dictionary
            shops[shop_id] = post_data

            # Save the shops to the JSON file
            save_shops()

            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Shop created successfully", "shop_id": shop_id}).encode())

        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid request body"}).encode())

    def do_PUT(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        if parsed_path.path.startswith('/shop'):
            if 'id' in query_params:
                shop_id = query_params['id'][0]
                if shop_id.isdigit():
                    if shop_id in shops:
                        content_length = int(self.headers['Content-Length'])
                        if content_length == 0:
                            self.send_response(400)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({"error": "Request body is empty"}).encode())
                            return

                        put_data = self.rfile.read(content_length)
                        try:
                            put_data = json.loads(put_data)
                            if not isinstance(put_data, dict):
                                raise ValueError("Invalid JSON format")
                        except ValueError as e:
                            self.send_response(400)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({"error": str(e)}).encode())
                            return

                        # Update the shop with the new data
                        shops[shop_id].update(put_data)

                        # Save the shops to the JSON file
                        save_shops()

                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"message": "Shop updated successfully"}).encode())
                        return
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Shop not found"}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        if parsed_path.path.startswith('/shops'):
            # Delete all shops
            shops.clear()

            # Save the empty shops to the JSON file
            save_shops()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "All shops deleted successfully"}).encode())
            return
        elif parsed_path.path.startswith('/shop'):
            if 'id' in query_params:
                shop_id = query_params['id'][0]
                if shop_id.isdigit():
                    if shop_id in shops:
                        # Delete the shop with the specified ID
                        del shops[shop_id]

                        # Save the shops to the JSON file
                        save_shops()

                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"message": "Shop deleted successfully"}).encode())
                        return
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Shop not found"}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()


if __name__ == '__main__':
    # Load existing shops from the JSON file
    shops = load_shops()
    run()
