package com.example.reco.controllers.dto;

import java.time.Instant;
import java.util.UUID;

public class RecommendationResponse {

    private final Long id;
    private final Long userId;
    private final Long itemId;
    private final Double score;
    private final Integer rank;
    private final String algoVersion;
    private final UUID runId;
    private final String reason;
    private final Instant generatedAt;

    public RecommendationResponse(
            Long id,
            Long userId,
            Long itemId,
            Double score,
            Integer rank,
            String algoVersion,
            UUID runId,
            String reason,
            Instant generatedAt
    ) {
        this.id = id;
        this.userId = userId;
        this.itemId = itemId;
        this.score = score;
        this.rank = rank;
        this.algoVersion = algoVersion;
        this.runId = runId;
        this.reason = reason;
        this.generatedAt = generatedAt;
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

    public Double getScore() {
        return score;
    }

    public Integer getRank() {
        return rank;
    }

    public String getAlgoVersion() {
        return algoVersion;
    }

    public UUID getRunId() {
        return runId;
    }

    public String getReason() {
        return reason;
    }

    public Instant getGeneratedAt() {
        return generatedAt;
    }
}
