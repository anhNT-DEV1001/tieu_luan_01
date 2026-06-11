package com.ecommerce.diagram.order;

import java.math.BigDecimal;

public class OrderItem {
    private Long id;
    private Order order;
    private Long productId;
    private String productName;
    private String sku;
    private Integer quantity;
    private BigDecimal unitPrice;
    private BigDecimal lineTotal;
    private ProductSnapshot productSnapshot;

    public OrderItem() {
    }
}
