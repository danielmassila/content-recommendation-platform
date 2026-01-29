package com.example.reco.controllers;

import com.example.reco.controllers.dto.CreateRatingRequest;
import com.example.reco.controllers.dto.RatingResponse;
import com.example.reco.services.RatingService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
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
@RequestMapping("/api/v1")
public class RatingsController {

    private final RatingService ratingService;

    public RatingsController(RatingService ratingService) {
        this.ratingService = ratingService;
    }

    @GetMapping("/ratings")
    public List<RatingResponse> getAllRatings(@RequestParam(defaultValue = "50") int limit) {
        return ratingService.getAllRatings(limit);
    }

    @GetMapping("/ratings/{id}")
    public RatingResponse getRatingById(@PathVariable Long id) {
        return ratingService.getRatingById(id);
    }

    @GetMapping("/users/{userId}/ratings")
    public List<RatingResponse> getRatingsByUser(@PathVariable Long userId, @RequestParam(defaultValue = "50") int limit) {
        return ratingService.getRatingsByUser(userId, limit);
    }

    @GetMapping("/items/{itemId}/ratings")
    public List<RatingResponse> getRatingsByItem(@PathVariable Long itemId, @RequestParam(defaultValue = "50") int limit) {
        return ratingService.getRatingsByItem(itemId, limit);
    }

    @PostMapping("/ratings/{itemId}")
    @ResponseStatus(HttpStatus.CREATED)
    public RatingResponse rateItem(@PathVariable Long itemId, @Valid @RequestBody CreateRatingRequest request) {
        return ratingService.rateItem(itemId, request.getUserId(), request.getGrade());
    }

    @PutMapping("/ratings/{id}")
    public RatingResponse updateRating(@PathVariable Long id, @RequestParam Short newGrade) {
        return ratingService.updateRating(id, newGrade);
    }

}
