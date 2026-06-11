package com.ecommerce.diagram.payment;

import java.math.BigDecimal;

public class CreatePaymentRequest {
    private Long orderId;
    private String payerName;
    private BigDecimal amount;
    private String currency;
    private PaymentMethod method;
    private PaymentStatus status;
    private String transactionCode;
    private String source;

    public CreatePaymentRequest() {
    }
}
