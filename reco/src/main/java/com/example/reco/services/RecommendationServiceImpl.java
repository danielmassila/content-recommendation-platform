package com.example.reco.services;

import com.example.reco.controllers.dto.RecommendationResponse;
import com.example.reco.model.Recommendation;
import com.example.reco.repositories.RecommendationRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class RecommendationServiceImpl implements RecommendationService {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 50;

    private final RecommendationRepository recommendationRepository;

    public RecommendationServiceImpl(RecommendationRepository recommendationRepository) {
        this.recommendationRepository = recommendationRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public List<RecommendationResponse> getAllRecommendations(int limit) {
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);
        List<RecommendationResponse> recommendationList = recommendationRepository.findAll(PageRequest.of(0, myLimit))
                                                                  .stream()
                                                                  .map(r -> toResponse(r, true))
                                                                  .toList();
        return recommendationList;
    }

    @Override
    @Transactional(readOnly = true)
    public List<RecommendationResponse> getUserRecommendations(Long userId, int limit, boolean includeReason, String algo) {
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);

        List<Recommendation> recommendations;
        PageRequest page = PageRequest.of(0, myLimit);

        if (algo != null && !algo.isBlank()) {
            recommendations = recommendationRepository
                                      .findByUserIdAndAlgoVersion(userId, algo, page)
                                      .getContent();
        } else {
            recommendations = recommendationRepository
                                      .findByUserId(userId, page)
                                      .getContent();
        }

        return recommendations.stream()
                       .map(r -> toResponse(r, includeReason))
                       .toList();

    }
    private RecommendationResponse toResponse(Recommendation recommendation, boolean includeReason) {
        return new RecommendationResponse(
                recommendation.getId(),
                recommendation.getUser().getId(),
                recommendation.getItem().getId(),
                recommendation.getScore(),
                recommendation.getRank(),
                recommendation.getAlgoVersion(),
                recommendation.getRunId(),
                includeReason ? recommendation.getReason() : null,
                recommendation.getGeneratedAt()
        );
    }
