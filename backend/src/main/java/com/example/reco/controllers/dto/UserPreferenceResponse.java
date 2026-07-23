package com.example.reco.controllers.dto;

import java.time.Instant;

public class UserPreferenceResponse {
    private Long id;
    private Long userId;
    private String type;
    private String value;
    private Instant createdAt;

    public UserPreferenceResponse(Long id, Long userId, String type, String value, Instant createdAt) {
        this.id = id;
        this.userId = userId;
        this.type = type;
        this.value = value;
        this.createdAt = createdAt;
    }

    public Long getId() {
        return id;
    }

    public Long getUserId() {
        return userId;
    }

    public String getType() {
        return type;
    }

    public String getValue() {
        return value;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
