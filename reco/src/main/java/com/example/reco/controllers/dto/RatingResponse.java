package com.example.reco.controllers.dto;

import java.time.Instant;

public class RatingResponse {
    private final Long id;
    private final Long userId;
    private final Long itemId;
    private final Short rating;
    private final Instant createdAt;

    public RatingResponse(Long id, Long userId, Long itemId, Short rating, Instant createdAt) {
        this.id = id;
        this.userId = userId;
        this.itemId = itemId;
        this.rating = rating;
        this.createdAt = createdAt;
    }

    public Long getId() {
        return id;
    }

    public Long getUserId() {
        return userId;
    }

    public Long getItemId() {
        return itemId;
    }

    public Short getRating() {
        return rating;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
