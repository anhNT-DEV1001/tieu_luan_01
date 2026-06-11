package com.ecommerce.diagram.gateway;

public class HealthcheckResponse {
    private String service;
    private String status;
    private ServiceRegistry upstreams;

    public HealthcheckResponse() {
    }
}
