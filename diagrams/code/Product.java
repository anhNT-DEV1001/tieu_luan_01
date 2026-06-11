package com.ecommerce.diagram.product;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

public class Product {
    private Long id;
    private String sku;
    private String name;
    private String slug;
    private String category;
    private String brand;
    private BigDecimal price;
    private BigDecimal discountPrice;
    private String currency;
    private Integer stockQuantity;
    private Integer safetyStock;
    private BigDecimal rating;
    private Integer weightGrams;
    private ProductDimensions dimensions;
    private String color;
    private String material;
    private String size;
    private String originCountry;
    private Integer warrantyMonths;
    private String description;
    private List<String> tags;
    private Map<String, Object> attributes;
    private String thumbnailUrl;
    private ProductStatus status;
    private OffsetDateTime publishedAt;
    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    public Product() {
    }
}
