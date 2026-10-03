CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

CREATE TABLE customers (
	name VARCHAR(160) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	phone VARCHAR(40), 
	source VARCHAR(30) NOT NULL, 
	source_id VARCHAR(120) NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source, source_id)
)

;

CREATE TABLE products (
	family VARCHAR(160) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	official_url TEXT, 
	image_url TEXT, 
	id UUID NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE documents (
	title VARCHAR(200) NOT NULL, 
	source_url TEXT NOT NULL, 
	version VARCHAR(80) NOT NULL, 
	published_on DATE, 
	family VARCHAR(160) NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	storage_path TEXT, 
	active BOOLEAN NOT NULL, 
	approved BOOLEAN NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	error VARCHAR(160), 
	kind VARCHAR(30) NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source_url, version)
)

;

CREATE TABLE sla_rules (
	severity VARCHAR(20) NOT NULL, 
	response_minutes INTEGER NOT NULL, 
	resolution_minutes INTEGER NOT NULL, 
	timezone VARCHAR(80) NOT NULL, 
	weekdays JSON NOT NULL, 
	start_hour INTEGER NOT NULL, 
	end_hour INTEGER NOT NULL, 
	official BOOLEAN NOT NULL, 
	escalation_minutes INTEGER NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (severity)
)

;

CREATE TABLE issue_categories (
	name VARCHAR(60) NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	PRIMARY KEY (name)
)

;

CREATE TABLE sync_events (
	source VARCHAR(30) NOT NULL, 
	record_id VARCHAR(120), 
	status VARCHAR(30) NOT NULL, 
	error VARCHAR(100), 
	last_synced_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE audit_events (
	actor_id UUID, 
	action VARCHAR(100) NOT NULL, 
	resource_id VARCHAR(120), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE customer_profiles (
	id UUID NOT NULL, 
	customer_id UUID, 
	display_name VARCHAR(160) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id)
)

;
CREATE INDEX ix_customer_profiles_customer_id ON customer_profiles (customer_id);

CREATE TABLE product_models (
	product_id UUID NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	source VARCHAR(30) NOT NULL, 
	source_id VARCHAR(120) NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source, source_id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
)

;
CREATE INDEX ix_product_models_product_id ON product_models (product_id);

CREATE TABLE purchases (
	customer_id UUID NOT NULL, 
	source VARCHAR(30) NOT NULL, 
	source_id VARCHAR(120) NOT NULL, 
	invoice_number VARCHAR(120) NOT NULL, 
	purchased_on DATE NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	amount NUMERIC(14, 2), 
	payment_status VARCHAR(80), 
	last_synced_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source, source_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id)
)

;
CREATE INDEX ix_purchases_customer_id ON purchases (customer_id);

CREATE TABLE document_chunks (
	document_id UUID NOT NULL, 
	text TEXT NOT NULL, 
	page INTEGER, 
	section VARCHAR(200), 
	embedding JSON NOT NULL, 
	embedding_model VARCHAR(120) NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
)

;
CREATE INDEX ix_document_chunks_document_id ON document_chunks (document_id);

CREATE TABLE development_credentials (
	user_id UUID NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES customer_profiles (id), 
	UNIQUE (email)
)

;

CREATE TABLE purchase_items (
	purchase_id UUID NOT NULL, 
	model_id UUID NOT NULL, 
	source_line_id VARCHAR(120) NOT NULL, 
	quantity INTEGER NOT NULL, 
	amount NUMERIC(14, 2), 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (purchase_id, source_line_id), 
	FOREIGN KEY(purchase_id) REFERENCES purchases (id), 
	FOREIGN KEY(model_id) REFERENCES product_models (id)
)

;
CREATE INDEX ix_purchase_items_purchase_id ON purchase_items (purchase_id);

CREATE TABLE receipts (
	purchase_id UUID NOT NULL, 
	storage_path TEXT NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(purchase_id) REFERENCES purchases (id)
)

;
CREATE INDEX ix_receipts_purchase_id ON receipts (purchase_id);

CREATE TABLE document_models (
	document_id UUID NOT NULL, 
	model_id UUID NOT NULL, 
	PRIMARY KEY (document_id, model_id), 
	FOREIGN KEY(document_id) REFERENCES documents (id), 
	FOREIGN KEY(model_id) REFERENCES product_models (id)
)

;

CREATE TABLE customer_products (
	customer_id UUID NOT NULL, 
	model_id UUID NOT NULL, 
	purchase_item_id UUID NOT NULL, 
	serial VARCHAR(120), 
	source_asset_id VARCHAR(120) NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (purchase_item_id, source_asset_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(model_id) REFERENCES product_models (id), 
	FOREIGN KEY(purchase_item_id) REFERENCES purchase_items (id)
)

;
CREATE INDEX ix_customer_products_customer_id ON customer_products (customer_id);
CREATE INDEX ix_customer_products_purchase_item_id ON customer_products (purchase_item_id);

CREATE TABLE warranties (
	customer_product_id UUID NOT NULL, 
	starts_on DATE, 
	ends_on DATE, 
	basis VARCHAR(40) NOT NULL, 
	evidence TEXT NOT NULL, 
	adjusted_by UUID, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (customer_product_id), 
	FOREIGN KEY(customer_product_id) REFERENCES customer_products (id)
)

;

CREATE TABLE chat_sessions (
	customer_id UUID NOT NULL, 
	customer_product_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(customer_product_id) REFERENCES customer_products (id)
)

;
CREATE INDEX ix_chat_sessions_customer_id ON chat_sessions (customer_id);

CREATE TABLE tickets (
	number VARCHAR(40) NOT NULL, 
	customer_id UUID NOT NULL, 
	customer_product_id UUID NOT NULL, 
	category VARCHAR(60) NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	description TEXT NOT NULL, 
	approved_summary TEXT, 
	status VARCHAR(30) NOT NULL, 
	idempotency_key UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	response_due_at TIMESTAMP WITH TIME ZONE, 
	resolution_due_at TIMESTAMP WITH TIME ZONE, 
	responded_at TIMESTAMP WITH TIME ZONE, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	sla_official BOOLEAN NOT NULL, 
	escalation_minutes INTEGER, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (customer_id, idempotency_key), 
	UNIQUE (number), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(customer_product_id) REFERENCES customer_products (id), 
	FOREIGN KEY(category) REFERENCES issue_categories (name)
)

;
CREATE INDEX ix_tickets_customer_id ON tickets (customer_id);

CREATE TABLE chat_messages (
	session_id UUID NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	content TEXT NOT NULL, 
	sources JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES chat_sessions (id)
)

;
CREATE INDEX ix_chat_messages_session_id ON chat_messages (session_id);

CREATE TABLE ticket_images (
	customer_id UUID NOT NULL, 
	ticket_id UUID, 
	storage_path TEXT NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id)
)

;
CREATE INDEX ix_ticket_images_customer_id ON ticket_images (customer_id);
CREATE INDEX ix_ticket_images_ticket_id ON ticket_images (ticket_id);

CREATE TABLE ticket_events (
	ticket_id UUID NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	note TEXT NOT NULL, 
	actor_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id)
)

;
CREATE INDEX ix_ticket_events_ticket_id ON ticket_events (ticket_id);

CREATE TABLE email_events (
	ticket_id UUID NOT NULL, 
	state VARCHAR(30) NOT NULL, 
	attempts INTEGER NOT NULL, 
	next_attempt_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	error VARCHAR(100), 
	delivered_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (ticket_id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id)
)

;
CREATE INDEX ix_email_events_ticket_id ON email_events (ticket_id);
