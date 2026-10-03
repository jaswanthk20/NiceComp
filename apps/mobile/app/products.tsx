import { Page, Loading, ErrorMessage, Card, Body } from "../src/components/ui";
import { useResource } from "../src/hooks/useResource";
import { Product } from "../src/types";
import { ProductCard } from "../src/features/products/ProductCard";
export default function Products() {
  const result = useResource<Product[]>("/products");
  return (
    <Page
      title="My products"
      subtitle="Information and support for the equipment you own."
    >
      {result.loading ? (
        <Loading />
      ) : result.error ? (
        <ErrorMessage message={result.error} retry={result.reload} />
      ) : result.data?.length ? (
        result.data.map((p) => <ProductCard key={p.id} product={p} />)
      ) : (
        <Card>
          <Body>
            No registered products yet. Contact support to associate your
            purchases.
          </Body>
        </Card>
      )}
    </Page>
  );
}
