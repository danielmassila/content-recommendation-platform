package com.example.reco.controllers;

import com.example.reco.auth.AuthenticatedUser;
import com.example.reco.controllers.dto.ChangePasswordRequest;
import com.example.reco.controllers.dto.CreateRatingRequest;
import com.example.reco.controllers.dto.RatingResponse;
import com.example.reco.controllers.dto.RecommendationResponse;
import com.example.reco.controllers.dto.UpdateUserPreferencesRequest;
import com.example.reco.controllers.dto.UpdateUserRequest;
import com.example.reco.controllers.dto.UserPreferenceResponse;
import com.example.reco.controllers.dto.UserResponse;
import com.example.reco.services.RatingService;
import com.example.reco.services.RecommendationService;
import com.example.reco.services.UserPreferenceService;
import com.example.reco.services.UserService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/me")
public class MeController {

    private final UserService userService;
    private final RatingService ratingService;
    private final UserPreferenceService userPreferenceService;
    private final RecommendationService recommendationService;

    public MeController(
            UserService userService,
            RatingService ratingService,
            UserPreferenceService userPreferenceService,
            RecommendationService recommendationService
    ) {
        this.userService = userService;
        this.ratingService = ratingService;
        this.userPreferenceService = userPreferenceService;
        this.recommendationService = recommendationService;
    }

    @GetMapping
    public UserResponse getProfile(@AuthenticationPrincipal AuthenticatedUser principal) {
        return userService.getUserById(principal.id());
    }

    @PutMapping
    public UserResponse updateProfile(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @Valid @RequestBody UpdateUserRequest request
    ) {
        return userService.updateUser(principal.id(), request);
    }

    @PutMapping("/password")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void changePassword(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @Valid @RequestBody ChangePasswordRequest request
    ) {
        userService.changePassword(principal.id(), request);
    }

    @GetMapping("/ratings")
    public List<RatingResponse> getRatings(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @RequestParam(defaultValue = "50") @Min(1) @Max(50) int limit
    ) {
        return ratingService.getRatingsByUser(principal.id(), limit);
    }

    @PutMapping("/ratings/{itemId}")
    public RatingResponse rateItem(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @PathVariable Long itemId,
            @Valid @RequestBody CreateRatingRequest request
    ) {
        return ratingService.rateItem(itemId, principal.id(), request.getGrade());
    }

    @GetMapping("/preferences")
    public List<UserPreferenceResponse> getPreferences(@AuthenticationPrincipal AuthenticatedUser principal) {
        return userPreferenceService.getUserPreferences(principal.id());
    }

    @PutMapping("/preferences")
    public List<UserPreferenceResponse> replacePreferences(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @Valid @RequestBody UpdateUserPreferencesRequest request
    ) {
        return userPreferenceService.replaceUserPreferences(principal.id(), request);
    }

    @GetMapping("/recommendations")
    public List<RecommendationResponse> getRecommendations(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @RequestParam(defaultValue = "20") @Min(1) @Max(50) int limit,
            @RequestParam(defaultValue = "false") boolean includeReason,
            @RequestParam(required = false) String algo
    ) {
        return recommendationService.getUserRecommendations(principal.id(), limit, includeReason, algo);
    }

    @PostMapping("/recommendations/recompute")
    public List<RecommendationResponse> recomputeRecommendations(
            @AuthenticationPrincipal AuthenticatedUser principal,
            @RequestParam(defaultValue = "20") @Min(1) @Max(50) int limit,
            @RequestParam(defaultValue = "false") boolean includeReason,
            @RequestParam(required = false) String algo
    ) {
        return recommendationService.recomputeRecommendationsForUser(principal.id(), limit, includeReason, algo);
    }
}
