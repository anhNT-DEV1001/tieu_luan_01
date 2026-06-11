package com.ecommerce.diagram.ai;

import java.util.Map;

public class SearchHit {
    private String entityType;
    private String entityId;
    private String title;
    private Double score;
    private Map<String, Object> payload;

    public SearchHit() {
    }
}
