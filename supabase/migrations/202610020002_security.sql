-- API role cannot be selected by a browser JWT. API verifies the session with Supabase Auth,
-- sets the subject transaction-locally and assumes this non-bypass role.
DO $$ BEGIN CREATE ROLE nice_api NOLOGIN NOBYPASSRLS; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
GRANT nice_api TO postgres;
GRANT USAGE ON SCHEMA public TO nice_api, authenticated;
GRANT USAGE ON SCHEMA extensions TO nice_api, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nice_api;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
REVOKE ALL ON development_credentials FROM authenticated, nice_api;

CREATE OR REPLACE FUNCTION public.current_customer() RETURNS uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,pg_temp AS $$
  SELECT customer_id FROM customer_profiles WHERE id=auth.uid()
$$;
CREATE OR REPLACE FUNCTION public.is_staff() RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,pg_temp AS $$
  SELECT EXISTS(SELECT 1 FROM customer_profiles WHERE id=auth.uid() AND role IN ('support','admin'))
$$;
CREATE OR REPLACE FUNCTION public.is_admin() RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,pg_temp AS $$
  SELECT EXISTS(SELECT 1 FROM customer_profiles WHERE id=auth.uid() AND role='admin')
$$;
REVOKE ALL ON FUNCTION current_customer(),is_staff(),is_admin() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION current_customer(),is_staff(),is_admin() TO authenticated,nice_api;

DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY['customers','customer_profiles','development_credentials','products','product_models','purchases','purchase_items','customer_products','warranties','receipts','documents','document_models','document_chunks','chat_sessions','chat_messages','sla_rules','issue_categories','tickets','ticket_images','ticket_events','email_events','sync_events','audit_events'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
  END LOOP;
END $$;

CREATE POLICY profiles_read ON customer_profiles FOR SELECT TO authenticated,nice_api USING(id=auth.uid() OR is_admin());
CREATE POLICY profiles_update ON customer_profiles FOR UPDATE TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY customers_read ON customers FOR SELECT TO authenticated,nice_api USING(id=current_customer() OR is_staff());
CREATE POLICY customers_admin ON customers FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY products_read ON products FOR SELECT TO authenticated,nice_api USING(true);
CREATE POLICY products_write ON products FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY models_read ON product_models FOR SELECT TO authenticated,nice_api USING(true);
CREATE POLICY models_write ON product_models FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY purchase_read ON purchases FOR SELECT TO authenticated,nice_api USING(customer_id=current_customer() OR is_staff());
CREATE POLICY purchase_write ON purchases FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY items_read ON purchase_items FOR SELECT TO authenticated,nice_api USING(EXISTS(SELECT 1 FROM purchases p WHERE p.id=purchase_id));
CREATE POLICY items_write ON purchase_items FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY assets_read ON customer_products FOR SELECT TO authenticated,nice_api USING(customer_id=current_customer() OR is_staff());
CREATE POLICY assets_write ON customer_products FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY warranty_read ON warranties FOR SELECT TO authenticated,nice_api USING(EXISTS(SELECT 1 FROM customer_products a WHERE a.id=customer_product_id));
CREATE POLICY warranty_write ON warranties FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY receipt_read ON receipts FOR SELECT TO authenticated,nice_api USING(EXISTS(SELECT 1 FROM purchases p WHERE p.id=purchase_id));
CREATE POLICY receipt_write ON receipts FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());

CREATE POLICY documents_read ON documents FOR SELECT TO authenticated,nice_api USING((active AND approved AND status='indexed') OR is_staff());
CREATE POLICY documents_write ON documents FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY doc_models_read ON document_models FOR SELECT TO authenticated,nice_api USING(EXISTS(SELECT 1 FROM documents d WHERE d.id=document_id));
CREATE POLICY doc_models_write ON document_models FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY chunks_read ON document_chunks FOR SELECT TO authenticated,nice_api USING(is_staff() OR EXISTS(
 SELECT 1 FROM documents d JOIN document_models dm ON dm.document_id=d.id JOIN customer_products a ON a.model_id=dm.model_id
 WHERE d.id=document_chunks.document_id AND d.active AND d.approved AND a.customer_id=current_customer()));
CREATE POLICY chunks_write ON document_chunks FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());

CREATE POLICY sessions_read ON chat_sessions FOR SELECT TO authenticated,nice_api USING(customer_id=current_customer() OR is_staff());
CREATE POLICY sessions_insert ON chat_sessions FOR INSERT TO nice_api WITH CHECK(customer_id=current_customer() AND EXISTS(SELECT 1 FROM customer_products a WHERE a.id=customer_product_id AND a.customer_id=current_customer()));
CREATE POLICY messages_read ON chat_messages FOR SELECT TO authenticated,nice_api USING(EXISTS(SELECT 1 FROM chat_sessions s WHERE s.id=session_id));
CREATE POLICY messages_insert ON chat_messages FOR INSERT TO nice_api WITH CHECK(EXISTS(SELECT 1 FROM chat_sessions s WHERE s.id=session_id AND s.customer_id=current_customer()));
CREATE POLICY sla_read ON sla_rules FOR SELECT TO authenticated,nice_api USING(is_staff() OR official);
-- API needs unapproved rules to calculate internally without displaying unofficial targets.
CREATE POLICY sla_api_read ON sla_rules FOR SELECT TO nice_api USING(true);
CREATE POLICY sla_write ON sla_rules FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY categories_read ON issue_categories FOR SELECT TO authenticated,nice_api USING(true);
CREATE POLICY categories_write ON issue_categories FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY tickets_read ON tickets FOR SELECT TO authenticated,nice_api USING(customer_id=current_customer() OR is_staff());
CREATE POLICY tickets_insert ON tickets FOR INSERT TO nice_api WITH CHECK(customer_id=current_customer() AND EXISTS(SELECT 1 FROM customer_products a WHERE a.id=customer_product_id AND a.customer_id=current_customer()));
CREATE POLICY tickets_update ON tickets FOR UPDATE TO nice_api USING(is_staff()) WITH CHECK(is_staff());
CREATE POLICY images_read ON ticket_images FOR SELECT TO authenticated,nice_api USING(customer_id=current_customer() OR is_staff());
CREATE POLICY images_insert ON ticket_images FOR INSERT TO nice_api WITH CHECK(customer_id=current_customer() AND ticket_id IS NULL);
CREATE POLICY images_update ON ticket_images FOR UPDATE TO nice_api USING(customer_id=current_customer()) WITH CHECK(customer_id=current_customer() AND EXISTS(SELECT 1 FROM tickets t WHERE t.id=ticket_id AND t.customer_id=current_customer()));
CREATE POLICY events_read ON ticket_events FOR SELECT TO authenticated,nice_api USING(EXISTS(SELECT 1 FROM tickets t WHERE t.id=ticket_id));
CREATE POLICY events_insert ON ticket_events FOR INSERT TO nice_api WITH CHECK(actor_id=auth.uid() AND EXISTS(SELECT 1 FROM tickets t WHERE t.id=ticket_id));
CREATE POLICY email_read ON email_events FOR SELECT TO authenticated,nice_api USING(EXISTS(SELECT 1 FROM tickets t WHERE t.id=ticket_id));
CREATE POLICY email_insert ON email_events FOR INSERT TO nice_api WITH CHECK(EXISTS(SELECT 1 FROM tickets t WHERE t.id=ticket_id AND t.customer_id=current_customer()));
CREATE POLICY email_update ON email_events FOR UPDATE TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY sync_read ON sync_events FOR SELECT TO authenticated,nice_api USING(is_staff());
CREATE POLICY sync_write ON sync_events FOR ALL TO nice_api USING(is_admin()) WITH CHECK(is_admin());
CREATE POLICY audit_read ON audit_events FOR SELECT TO authenticated,nice_api USING(is_admin());
CREATE POLICY audit_insert ON audit_events FOR INSERT TO nice_api WITH CHECK(actor_id=auth.uid());

-- Private bucket: browser clients cannot list, upload, delete or read raw objects.
-- The backend authorizes the receipt/image record before returning a 120-second signed URL.
INSERT INTO storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
VALUES('private-support','private-support',false,20000000,ARRAY['application/pdf','image/jpeg'])
ON CONFLICT(id) DO UPDATE SET public=false;

ALTER TABLE document_chunks ADD COLUMN embedding_vector extensions.vector(768);
CREATE INDEX chunks_embedding_hnsw ON document_chunks USING hnsw(embedding_vector extensions.vector_cosine_ops);
CREATE INDEX email_pending_idx ON email_events(state,next_attempt_at);
CREATE INDEX ticket_due_idx ON tickets(status,response_due_at);
ALTER TABLE customer_profiles ADD CONSTRAINT valid_role CHECK(role IN ('customer','support','admin'));
ALTER TABLE tickets ADD CONSTRAINT valid_severity CHECK(severity IN ('Critical','High','Medium','Low'));
ALTER TABLE tickets ADD CONSTRAINT valid_status CHECK(status IN ('Open','Acknowledged','In Progress','Waiting for Customer','Resolved','Closed'));
ALTER TABLE warranties ADD CONSTRAINT valid_warranty_dates CHECK(ends_on IS NULL OR starts_on IS NULL OR ends_on>=starts_on);
ALTER TABLE purchase_items ADD CONSTRAINT positive_quantity CHECK(quantity>0);
ALTER TABLE sla_rules ADD CONSTRAINT valid_sla_hours CHECK(start_hour>=0 AND end_hour<=24 AND start_hour<end_hour);
ALTER TABLE sla_rules ADD CONSTRAINT valid_sla_targets CHECK(response_minutes>0 AND resolution_minutes>=response_minutes AND escalation_minutes>0);

CREATE OR REPLACE FUNCTION public.on_auth_user_created() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=public,pg_temp AS $$
BEGIN
 INSERT INTO customer_profiles(id,display_name,role) VALUES(new.id,'Customer','customer') ON CONFLICT(id) DO NOTHING;
 RETURN new;
END $$;
REVOKE ALL ON FUNCTION on_auth_user_created() FROM PUBLIC;
CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION on_auth_user_created();
