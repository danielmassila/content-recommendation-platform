package com.example.reco.common.exceptions;

public class RecommendationJobException extends RuntimeException {
    public RecommendationJobException(String message) {
        super(message);
    }

    public RecommendationJobException(String message, Throwable cause) {
        super(message, cause);
    }
}
