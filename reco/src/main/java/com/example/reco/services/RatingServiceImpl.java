package com.example.reco.services;

import com.example.reco.common.exceptions.BadRequestException;
import com.example.reco.common.exceptions.ConflictException;
import com.example.reco.common.exceptions.NotFoundException;
import com.example.reco.controllers.dto.RatingResponse;
import com.example.reco.model.Item;
import com.example.reco.model.Rating;
import com.example.reco.model.User;
import com.example.reco.repositories.ItemRepository;
import com.example.reco.repositories.RatingRepository;
import com.example.reco.repositories.UserRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

@Service
@Transactional
public class RatingServiceImpl implements RatingService {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 50;
    private static final BigDecimal MIN_GRADE = BigDecimal.ONE;
    private static final BigDecimal MAX_GRADE = BigDecimal.valueOf(5);

    private final RatingRepository ratingRepository;
    private final ItemRepository itemRepository;
    private final UserRepository userRepository;

    public RatingServiceImpl(RatingRepository ratingRepository, ItemRepository itemRepository, UserRepository userRepository) {
        this.ratingRepository = ratingRepository;
        this.itemRepository = itemRepository;
        this.userRepository = userRepository;
    }

    private static void validateGrade(BigDecimal grade) {
        if (grade == null
                    || grade.compareTo(MIN_GRADE) < 0
                    || grade.compareTo(MAX_GRADE) > 0) {
            throw new BadRequestException("Invalid grade attributed: " + grade);
        }
    }

    @Override
    @Transactional(readOnly = true)
    public List<RatingResponse> getAllRatings(int limit) {
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);

        return ratingRepository.findAll(PageRequest.of(0, myLimit))
                       .stream()
                       .map(this::toResponse)
                       .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public RatingResponse getRatingById(Long id) {
        Rating rating = ratingRepository.findById(id)
                                .orElseThrow(() -> new NotFoundException("Rating with id " + id + " not found"));
        return toResponse(rating);
    }

    @Override
    @Transactional(readOnly = true)
    public List<RatingResponse> getRatingsByUser(Long userId, int limit) { // add a safeguard?
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);
        Page<Rating> page = ratingRepository.findByUserId(userId, PageRequest.of(0, myLimit));
        return page.stream().map(this::toResponse).toList();
    }

    @Override
    @Transactional(readOnly = true)
    public List<RatingResponse> getRatingsByItem(Long itemId, int limit) { // add a safeguard?
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);
        Page<Rating> page = ratingRepository.findByItemId(itemId, PageRequest.of(0, myLimit));
        return page.stream().map(this::toResponse).toList();
    }

    @Override
    public RatingResponse rateItem(Long itemId, Long userId, BigDecimal grade) {
        validateGrade(grade);

        Item item = itemRepository.findById(itemId)
                            .orElseThrow(() -> new NotFoundException("Item with id " + itemId + " not found"));
        User user = userRepository.findById(userId)
                            .orElseThrow(() -> new NotFoundException("User with id " + userId + " not found"));

        ratingRepository.findByUserIdAndItemId(userId, itemId).ifPresent(existing -> {
            throw new ConflictException("User already rated this item");
        });

        Rating saved = ratingRepository.save(new Rating(user, item, grade));
        return toResponse(saved);
    }

    @Override
    public RatingResponse updateRating(Long id, BigDecimal newGrade) {
        validateGrade(newGrade);

        Rating rating = ratingRepository.findById(id)
                                .orElseThrow(() -> new NotFoundException("Rating with id " + id + " not found"));

        rating.setRating(newGrade);
        return toResponse(ratingRepository.save(rating));
    }

    private RatingResponse toResponse(Rating rating) {
        return new RatingResponse(
                rating.getId(),
                rating.getUser().getId(),
                rating.getItem().getId(),
                rating.getRating(),
                rating.getCreatedAt()
        );
    }

}
