package com.ecommerce.diagram.payment;

import com.ecommerce.diagram.order.Order;
import java.math.BigDecimal;
import java.time.OffsetDateTime;

public class Payment {
    private Long id;
    private Long orderId;
    private Order order;
    private String payerName;
    private BigDecimal amount;
    private String currency;
    private PaymentMethod method;
    private PaymentStatus status;
    private String transactionCode;
    private GatewayResponse gatewayResponse;
    private OffsetDateTime paidAt;
    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    public Payment() {
    }
}
