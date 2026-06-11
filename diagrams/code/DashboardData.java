package com.ecommerce.diagram.shared;

import com.ecommerce.diagram.order.Order;
import com.ecommerce.diagram.order.OrderSummary;
import com.ecommerce.diagram.payment.Payment;
import com.ecommerce.diagram.payment.PaymentSummary;
import com.ecommerce.diagram.product.Product;
import com.ecommerce.diagram.product.ProductSummary;
import com.ecommerce.diagram.user.UserProfile;
import com.ecommerce.diagram.user.UserSummary;
import java.util.List;

public class DashboardData {
    private List<UserProfile> users;
    private UserSummary userSummary;
    private List<Product> products;
    private ProductSummary productSummary;
    private List<Order> orders;
    private OrderSummary orderSummary;
    private List<Payment> payments;
    private PaymentSummary paymentSummary;

    public DashboardData() {
    }
}
