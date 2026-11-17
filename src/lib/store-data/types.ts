/**
 * One row of the store's order export. The dataset's grain is the order
 * line item: an order with two products appears as two rows that share an
 * `orderId`.
 */
export interface OrderLineItem {
  orderId: string;
  lineItemId: string;
  /** Order date, `YYYY-MM-DD`. */
  orderDate: string;
  customerId: string;
  /** True when this order was placed by a customer who had ordered before. */
  isRepeatCustomer: boolean;
  productId: string;
  productTitle: string;
  productCategory: string;
  /** Raw variant label, e.g. `"M / Black"` or `"One Size / Charcoal"`. */
  variant: string;
  /** Size half of the variant, e.g. `"M"`. */
  size: string;
  /** Colour half of the variant, e.g. `"Black"`. */
  color: string;
  quantity: number;
  unitPrice: number;
  discountAmount: number;
  /** `quantity * unitPrice - discountAmount`. */
  lineTotal: number;
  salesChannel: string;
  fulfillmentStatus: string;
  returned: boolean;
  /** Return date, `YYYY-MM-DD`, or `null` when the item was not returned. */
  returnDate: string | null;
  returnReason: string | null;
  /** Amount refunded for this line; `0` when not returned. */
  refundAmount: number;
}
