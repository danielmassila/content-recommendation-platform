package com.example.reco.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "recommendations", uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "item_id"}))
public class Recommendation {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "item_id", nullable = false)
    private Item item;

    @Column(nullable = false)
    private Double score;

    @Column(nullable = false)
    private Integer rank;

    @Column(name = "algo_version", nullable = false)
    private String algoVersion;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private String reason;

    @Column(name = "run_id")
    private UUID runId;

    @Column(name = "generated_at", nullable = false, updatable = false)
    private Instant generatedAt;


    @PrePersist
    protected void onCreate() {
        this.generatedAt = Instant.now();
    }

    public Recommendation() {
    }

    public Recommendation(
            User user,
            Item item,
            Double score,
            Integer rank,
            String algoVersion,
            UUID runId,
            String reason
    ) {
        this.user = user;
        this.item = item;
        this.score = score;
        this.rank = rank;
        this.algoVersion = algoVersion;
        this.runId = runId;
    }


    public Instant getGeneratedAt() {
        return generatedAt;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }

    public String getAlgoVersion() {
        return algoVersion;
    }

    public Integer getRank() {
        return rank;
    }

    public Double getScore() {
        return score;
    }

    public Item getItem() {
        return item;
    }

    public User getUser() {
        return user;
    }

    public Long getId() {
        return id;
    }

    public UUID getRunId() {
        return runId;
    }
}
