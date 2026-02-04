package com.example.reco.services;

import com.example.reco.controllers.dto.RecommendationResponse;
import com.example.reco.model.Recommendation;

import java.util.List;

public interface RecommendationService {

    List<RecommendationResponse> getAllRecommendations(int limit);

    List<RecommendationResponse> getUserRecommendations(Long userId, int limit, boolean includeReason, String algo);

    void recomputeRecommendationsForUser(Long userId);

    void dismissItemForUser(Long userId, Long itemId);
}
