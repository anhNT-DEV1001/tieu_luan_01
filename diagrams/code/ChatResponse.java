package com.ecommerce.diagram.ai;

import java.util.List;
import java.util.Map;

public class ChatResponse {
    private String intent;
    private String response;
    private Double confidence;
    private List<Map<String, Object>> sources;

    public ChatResponse() {
    }
}
