# POS and Odoo activation

The public website reports Odoo SaaS 19.3. The implemented adapter uses the documented Odoo 19 JSON-2 transport, **not an assumed XML-RPC integration**. It remains disabled until company-specific access and field mapping are verified.

## Information Nice Compressors must provide

1. Confirm that this is the same Odoo database that holds POS/orders/invoices, and provide its authenticated base URL and database name.
2. Confirm external API entitlement. Odoo's published documentation restricts external API access to eligible Custom plans.
3. Create a dedicated least-privilege integration user and an API key. Put the key directly in a secret manager or the backend `.env`; do not send it in mobile code or chat.
4. Provide the database's authenticated `/doc` schema for the relevant models, including installed module/custom field names and read permissions.
5. Confirm customer identity matching, account-ownership verification, order/invoice relationships, line IDs, product variant IDs, currencies, payment statuses and how multiple serialized units on one line are represented.
6. Confirm serial/lot links and explicit warranty fields. If duration-based warranty is required, provide approved commencement/date arithmetic rules, exclusions and authorized evidence sources.
7. Confirm the invoice/receipt export mechanism and permissions. The adapter does not presume a PDF-report URL. Private receipt PDF upload is already available as an interim path.
8. Agree on incremental export domains/batch size, time zone, update/cancellation behavior and reconciliation procedures. The current adapter fails instead of truncating a batch above 10,000 rows.

## Connector contract

`POSConnector` has `getCustomer`, `getCustomerPurchases`, `getPurchase`, `getReceipt`, `getPurchasedProducts`, `getWarrantyInformation`, `syncCustomers`, `syncProducts` and `syncPurchases` methods. Implementations:

- `CSVImportConnector`: validates a CSV or JSON canonical export and exposes its customer/order/asset records. Receipt bytes are imported separately.
- `DevelopmentTestConnector`: accepts the same fixture shape, and explicitly refuses production mode.
- `OdooConnector`: verified JSON-2 calls; model/field names come from an operator-supplied mapping, not assumptions about the private database. The canonical export can be a company-approved read-only view/model or an upstream export. If no such model exists, use CSV or implement a company-specific relational adapter after inspecting the schema.

This is a real transport and synchronization boundary, not a claim that the unknown company installation is already connected. In particular, the current generic connector does not automatically join arbitrary standard/custom Odoo models into the canonical export.

## Configuration

Set `ODOO_BASE_URL`, `ODOO_DATABASE`, `ODOO_API_KEY`, `ODOO_MAPPING_FILE` and, **only after verification**, `ODOO_API_VERIFIED=true`. `ODOO_USERNAME` records the intended integration account but is not sent as a JSON-2 password credential.

The mapping JSON must contain:

- `api_version`: `19-json-2`
- `resources.customers`, `.products`, `.purchases`, `.canonical_export`: each contains the **verified** `model` and permitted `fields` array.
- Optional `resources.receipts` / `.warranties` and their verified link fields.
- `customer_field`, optionally `receipt_purchase_field` and `warranty_asset_field`.
- `canonical_export_fields`: a dictionary mapping every canonical field below to its actual scalar field in the verified export resource.

No fictitious private model names are shipped. Validate authenticated calls in a nonproduction database, import a small approved batch, check ownership and receipt/warranty provenance, and then enable periodic operation. The admin interface currently provides explicit sync; scheduling is an operator deployment responsibility.

Official API reference: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html

## CSV / JSON interim export

Upload from Admin → Integrations. Create product mappings first in Admin → Records. A row represents an asset linked to an order line; the stable asset ID distinguishes several serialized units on one line.

| Field | Required / meaning |
| --- | --- |
| `customer_id` | Required stable source customer ID |
| `customer_name`, `customer_email` | Required verified source identity |
| `order_id`, `invoice_number`, `purchased_on` | Required order identity and ISO date |
| `currency` | Required three-letter uppercase code |
| `amount`, `payment_status` | Optional order amount and source status |
| `line_id`, `model_source_id` | Required stable line ID and already mapped product model |
| `quantity` | Positive source line quantity |
| `asset_id`, `serial` | Stable source asset ID; serial optional |
| `warranty_start`, `warranty_end`, `warranty_evidence` | Optional; all three needed before importing warranty dates |

Unknown columns are rejected. Maximum upload: 5 MB / 10,000 rows. Every row is validated before synchronization. Source/customer ownership conflicts or unknown product mappings roll back the batch. Unique keys prevent duplicate purchases, purchase lines and customer assets. Sync events record source, order ID, status, time and safe error labels.

Customer login association is a separate administrator action. Matching email strings automatically is insufficient proof of account ownership. No arbitrary customer search is exposed to customers.

Receipt imports use `POST /admin/receipts/{purchase_id}` or Admin → Records. The server validates PDF content, saves it privately and records an audit event.
