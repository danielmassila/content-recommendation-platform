package com.example.reco.controllers.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public class CreateRecommendationRequest {

    @NotNull(message = "userId is required")
    private Long userId;

    @NotNull(message = "itemId is required")
    private Long itemId;

    @NotNull(message = "score is required")
    private Double score;

    @NotNull(message = "rank is required")
    @Min(value = 1, message = "rank must be >= 1")
    private Integer rank;

    @NotNull(message = "algoVersion is required")
    private String algoVersion;

    private String reason;

    public CreateRecommendationRequest() {
    }

    public CreateRecommendationRequest(
            Long userId,
            Long itemId,
            Double score,
            Integer rank,
            String algoVersion,
            String reason
    ) {
        this.userId = userId;
        this.itemId = itemId;
        this.score = score;
        this.rank = rank;
        this.algoVersion = algoVersion;
        this.reason = reason;
    }

    public Long getUserId() {
        return userId;
    }

    public Long getItemId() {
        return itemId;
    }

    public Double getScore() {
        return score;
    }

    public Integer getRank() {
        return rank;
    }

    public String getAlgoVersion() {
        return algoVersion;
    }

    public String getReason() {
        return reason;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public void setItemId(Long itemId) {
        this.itemId = itemId;
    }

    public void setScore(Double score) {
        this.score = score;
    }

    public void setRank(Integer rank) {
        this.rank = rank;
    }

    public void setAlgoVersion(String algoVersion) {
        this.algoVersion = algoVersion;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }
}
