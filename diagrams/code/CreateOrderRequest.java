package com.ecommerce.diagram.order;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

public class CreateOrderRequest {
    private Long userId;
    private List<CreateOrderItemRequest> items;
    private String shippingAddress;
    private String shippingCity;
    private BigDecimal shippingFee;
    private OrderStatus status;
    private String notes;
    private Map<String, Object> metadata;

    public CreateOrderRequest() {
    }
}
