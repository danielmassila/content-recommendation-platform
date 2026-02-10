package com.example.reco.services;

import com.example.reco.controllers.dto.RecommendationResponse;

import java.util.List;

public interface RecommendationService {

    List<RecommendationResponse> getAllRecommendations(int limit, boolean includeReason);

    List<RecommendationResponse> getUserRecommendations(Long userId, int limit, boolean includeReason, String algo);

    List<RecommendationResponse> recomputeRecommendationsForUser(Long userId, int limit, boolean includeReason, String algo);

    void recomputeAllRecommendations();

    void runRecommendationJob(String mode);
}
