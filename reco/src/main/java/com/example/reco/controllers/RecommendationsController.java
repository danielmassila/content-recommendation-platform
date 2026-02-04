package com.example.reco.controllers;

import com.example.reco.controllers.dto.RecommendationResponse;
import com.example.reco.services.RecommendationService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
public class RecommendationsController {

    private RecommendationService recommendationService;

    public RecommendationsController(RecommendationService recommendationService) {
        this.recommendationService = recommendationService;
    }

    @GetMapping("/admin/recommendations")
    public List<RecommendationResponse> getAllRecommendations(@RequestParam(defaultValue = "10") int limit) {
        return recommendationService.getAllRecommendations(limit);
    }

    @GetMapping("/users/{userId}/recommendations")
    public List<RecommendationResponse> getUserRecommendations(
            @PathVariable Long userId,
            @RequestParam(name = "limit", defaultValue = "20") @Min(1) @Max(100) int limit,
            @RequestParam(name = "includeReason", defaultValue = "false") boolean includeReason,
            @RequestParam(name = "algo", required = false) String algo
    ) {
        return recommendationService.getUserRecommendations(userId, limit, includeReason, algo);
    }

    @PostMapping("/users/{userId}/recommendations/recompute")
    public ResponseEntity<Void> recomputeUserRecommendations(@PathVariable Long userId) {
        recommendationService.recomputeRecommendationsForUser(userId);
        return ResponseEntity.accepted().build();
    }

    @PostMapping("/users/{userId}/recommendations/{itemId}/dismiss")
    public ResponseEntity<Void> dismissRecommendation(
            @PathVariable Long userId,
            @PathVariable Long itemId
    ) {
        recommendationService.dismissItemForUser(userId, itemId);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/admin/recommendations/recompute")
    public ResponseEntity<Void> recomputeAllRecommendations() {
        recommendationService.recomputeAllRecommendations();
        return ResponseEntity.accepted().build();
    }

}
