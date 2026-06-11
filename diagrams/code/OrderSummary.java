package com.ecommerce.diagram.order;

import java.math.BigDecimal;

public class OrderSummary {
    private String service;
    private Integer totalOrders;
    private BigDecimal grossRevenue;
    private TopCustomer topCustomer;
    private BestSellingProduct bestSellingProduct;

    public OrderSummary() {
    }
}
