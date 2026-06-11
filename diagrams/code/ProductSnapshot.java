package com.ecommerce.diagram.order;

import java.math.BigDecimal;
import java.util.Map;

public class ProductSnapshot {
    private Long productId;
    private String sku;
    private String name;
    private String category;
    private String brand;
    private BigDecimal currentPrice;
    private Map<String, Object> rawData;

    public ProductSnapshot() {
    }
}
