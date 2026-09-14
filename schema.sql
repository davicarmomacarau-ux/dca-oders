DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS offers;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS restaurants;

CREATE TABLE restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    whatsapp VARCHAR(30),
    business_type VARCHAR(30) NOT NULL DEFAULT 'restaurant',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    customer_name VARCHAR(150) NOT NULL,
    customer_phone VARCHAR(30),
    order_type VARCHAR(20) NOT NULL DEFAULT 'delivery',
    address TEXT,
    payment_method VARCHAR(30),
    notes TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'new',
    total NUMERIC(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name VARCHAR(150) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10,2) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL
);

CREATE TABLE campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    title VARCHAR(180) NOT NULL,
    channel VARCHAR(30) NOT NULL DEFAULT 'whatsapp',
    objective VARCHAR(40) NOT NULL DEFAULT 'pedido',
    audience VARCHAR(150),
    message TEXT,
    budget NUMERIC(10,2) NOT NULL DEFAULT 0,
    expected_revenue NUMERIC(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    title VARCHAR(180) NOT NULL,
    message TEXT,
    audience VARCHAR(150),
    discount NUMERIC(10,2) NOT NULL DEFAULT 0,
    channel VARCHAR(30) NOT NULL DEFAULT 'whatsapp',
    whatsapp_url TEXT,
    forecast_score NUMERIC(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO restaurants (name, slug, whatsapp, business_type)
VALUES ('DCA Demo', 'dca-demo', '5588999999999', 'restaurant');

INSERT INTO categories (restaurant_id, name, sort_order)
SELECT id, 'Hambúrgueres', 1 FROM restaurants
WHERE slug='dca-demo'
AND NOT EXISTS (
    SELECT 1 FROM categories c
    WHERE c.restaurant_id=restaurants.id
      AND c.name='Hambúrgueres'
);

INSERT INTO categories (restaurant_id, name, sort_order)
SELECT id, 'Pizzas', 2 FROM restaurants
WHERE slug='dca-demo'
AND NOT EXISTS (
    SELECT 1 FROM categories c
    WHERE c.restaurant_id=restaurants.id
      AND c.name='Pizzas'
);

INSERT INTO categories (restaurant_id, name, sort_order)
SELECT id, 'Bebidas', 3 FROM restaurants
WHERE slug='dca-demo'
AND NOT EXISTS (
    SELECT 1 FROM categories c
    WHERE c.restaurant_id=restaurants.id
      AND c.name='Bebidas'
);

INSERT INTO products (restaurant_id, category_id, name, description, price)
SELECT r.id, c.id, 'X-Bacon', 'Hambúrguer, queijo e bacon.', 22.00
FROM restaurants r
JOIN categories c ON c.restaurant_id=r.id AND c.name='Hambúrgueres'
WHERE r.slug='dca-demo'
AND NOT EXISTS (
    SELECT 1 FROM products p
    WHERE p.restaurant_id=r.id AND p.name='X-Bacon'
);

INSERT INTO products (restaurant_id, category_id, name, description, price)
SELECT r.id, c.id, 'Pizza Calabresa', 'Pizza grande de calabresa e queijo.', 45.00
FROM restaurants r
JOIN categories c ON c.restaurant_id=r.id AND c.name='Pizzas'
WHERE r.slug='dca-demo'
AND NOT EXISTS (
    SELECT 1 FROM products p
    WHERE p.restaurant_id=r.id AND p.name='Pizza Calabresa'
);

INSERT INTO products (restaurant_id, category_id, name, description, price)
SELECT r.id, c.id, 'Refrigerante', 'Lata 350 ml.', 6.00
FROM restaurants r
JOIN categories c ON c.restaurant_id=r.id AND c.name='Bebidas'
WHERE r.slug='dca-demo'
AND NOT EXISTS (
    SELECT 1 FROM products p
    WHERE p.restaurant_id=r.id AND p.name='Refrigerante'
);
