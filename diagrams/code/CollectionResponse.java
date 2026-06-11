package com.ecommerce.diagram.shared;

import java.util.List;

public class CollectionResponse<T> {
    private Integer count;
    private List<T> results;

    public CollectionResponse() {
    }
}
