package com.example.reco.services;

import com.example.reco.controllers.dto.RatingResponse;

import java.util.List;

public interface RatingService {
    List<RatingResponse> getAllRatings(int limit);

    RatingResponse getRatingById(Long id);

    RatingResponse rateItem(Long item_id, Long user_id, Short grade);

    List<RatingResponse> getRatingsByUser(Long userId, int limit);

    List<RatingResponse> getRatingsByItem(Long itemId, int limit);

    RatingResponse updateRating(Long id, Short newGrade);

}
