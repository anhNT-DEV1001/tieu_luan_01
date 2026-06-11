package com.ecommerce.diagram.user;

import java.time.OffsetDateTime;
import java.util.Map;

public class UserProfile {
    private Long id;
    private String fullName;
    private String email;
    private String phone;
    private UserRole role;
    private UserStatus status;
    private Integer loyaltyPoints;
    private String address;
    private String city;
    private String country;
    private String avatarUrl;
    private Map<String, Object> metadata;
    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    public UserProfile() {
    }
}
