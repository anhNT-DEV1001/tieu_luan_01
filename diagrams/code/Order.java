package com.ecommerce.diagram.order;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

public class Order {
    private Long id;
    private Long userId;
    private String customerName;
    private String customerEmail;
    private String shippingAddress;
    private String shippingCity;
    private ShippingInfo shippingInfo;
    private OrderStatus status;
    private BigDecimal subtotalAmount;
    private BigDecimal shippingFee;
    private BigDecimal totalAmount;
    private String notes;
    private Map<String, Object> metadata;
    private List<OrderItem> items;
    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    public Order() {
    }
}
