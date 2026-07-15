package com.services;

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
import com.example.reco.services.RatingServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrowsExactly;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class RatingServiceImplTest {
    @Mock
    private RatingRepository ratingRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private ItemRepository itemRepository;

    @InjectMocks
    private RatingServiceImpl ratingService;

    @Test
    void shouldReturnEmptyListWhenNoRatingsExist() {
        when(ratingRepository.findAll(any(Pageable.class)))
                .thenReturn(Page.empty());

        var response = ratingService.getAllRatings(50);

        assertNotNull(response);
        assertTrue(response.isEmpty());
        verify(ratingRepository).findAll(any(Pageable.class));
    }

    @Test
    void shouldReturnMappedRatingsWhenRepositoryReturnsRatings() {
        User user = new User();
        user.setId(1L);

        Item item = new Item();
        item.setId(2L);

        Rating rating1 = new Rating(user, item, BigDecimal.valueOf(4));
        rating1.setId(10L);

        Rating rating2 = new Rating(user, item, BigDecimal.valueOf(5));
        rating2.setId(11L);

        when(ratingRepository.findAll(any(Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(rating1, rating2)));

        var response = ratingService.getAllRatings(10);

        assertEquals(2, response.size());

        assertEquals(10L, response.get(0).getId());
        assertEquals(1L, response.get(0).getUserId());
        assertEquals(2L, response.get(0).getItemId());
        assertEquals((short) 4, response.get(0).getRating());

        assertEquals(11L, response.get(1).getId());
        assertEquals((short) 5, response.get(1).getRating());

        verify(ratingRepository).findAll(any(Pageable.class));
    }

    @Test
    void shouldCapLimitWhenLimitIsTooHigh() {
        when(ratingRepository.findAll(any(Pageable.class)))
                .thenReturn(Page.empty());

        ratingService.getAllRatings(99999);

        ArgumentCaptor<Pageable> captor = ArgumentCaptor.forClass(Pageable.class);
        verify(ratingRepository).findAll(captor.capture());

        Pageable pageableUsed = captor.getValue();
        assertEquals(0, pageableUsed.getPageNumber());
        assertEquals(50, pageableUsed.getPageSize());
    }

    @Test
    void shouldThrowNotFoundWhenItemDoesNotExist() {
        // arrange step
        Long unexistingItemId = 5L;
        Long userId = 3L;
        BigDecimal grade = BigDecimal.valueOf(4);

        when(itemRepository.findById(unexistingItemId)).thenReturn(Optional.empty());

        // act and assert step
        assertThrowsExactly(NotFoundException.class, () -> ratingService.rateItem(unexistingItemId, userId, grade));

        verify(itemRepository).findById(unexistingItemId);
        verify(userRepository, never()).findById(userId);
        verify(ratingRepository, never()).save(any(Rating.class));
    }

    @Test
    void shouldThrowNotFoundWhenUserDoesNotExist() {
        Long unexistingUserId = 9L;
        Long itemId = 7L;
        BigDecimal grade = BigDecimal.valueOf(2);

        Item existingItem = new Item();
        existingItem.setId(itemId);

        when(itemRepository.findById(itemId)).thenReturn(Optional.of(existingItem));
        when(userRepository.findById(unexistingUserId)).thenReturn(Optional.empty());

        assertThrowsExactly(NotFoundException.class, () -> ratingService.rateItem(itemId, unexistingUserId, grade));

        verify(itemRepository).findById(itemId);
        verify(userRepository).findById(unexistingUserId);
        verify(ratingRepository, never()).save(any(Rating.class));
    }

    @Test
    void shouldThrowBadRequestWhenInvalidGradeRating() {
        BigDecimal invalidGrade = BigDecimal.valueOf(100);
        Long userId = 10L;
        Long itemId = 4L;

        assertThrowsExactly(BadRequestException.class, () -> ratingService.rateItem(itemId, userId, invalidGrade));

        verify(itemRepository, never()).findById(itemId);
        verify(userRepository, never()).findById(userId);
        verify(ratingRepository, never()).save(any(Rating.class));

    }

    @Test
    void shouldHandleValidGradeRating() {
        Long userId = 5L;
        Long itemId = 7L;
        BigDecimal grade = BigDecimal.valueOf(4);

        Item existingItem = new Item();
        existingItem.setId(itemId);

        User existingUser = new User();
        existingUser.setId(userId);

        when(itemRepository.findById(itemId)).thenReturn(Optional.of(existingItem));
        when(userRepository.findById(userId)).thenReturn(Optional.of(existingUser));
        when(ratingRepository.save(any(Rating.class))).thenAnswer(invocation -> invocation.getArgument(0));

        RatingResponse response = ratingService.rateItem(itemId, userId, grade);

        verify(itemRepository).findById(itemId);
        verify(userRepository).findById(userId);

        ArgumentCaptor<Rating> captor = ArgumentCaptor.forClass(Rating.class);
        verify(ratingRepository).save(captor.capture());

        Rating saved = captor.getValue();
        assertEquals(userId, saved.getUser().getId());
        assertEquals(itemId, saved.getItem().getId());
        assertEquals(grade, saved.getRating());

        assertNotNull(response);
        assertEquals(userId, response.getUserId());
        assertEquals(itemId, response.getItemId());
        assertEquals(grade, response.getRating());
    }

    @Test
    void shouldThrowConflictWhenUserAlreadyRatedItem() {
        Long userId = 1L;
        Long itemId = 1L;
        BigDecimal grade = BigDecimal.valueOf(4);

        Item item = new Item();
        item.setId(itemId);

        User user = new User();
        user.setId(userId);

        Rating existingRating = new Rating();
        existingRating.setId(99L);

        when(itemRepository.findById(itemId)).thenReturn(Optional.of(item));
        when(userRepository.findById(userId)).thenReturn(Optional.of(user));
        when(ratingRepository.findByUserIdAndItemId(userId, itemId)).thenReturn(Optional.of(existingRating));

        assertThrowsExactly(
                ConflictException.class,
                () -> ratingService.rateItem(itemId, userId, grade)
        );

        verify(itemRepository).findById(itemId);
        verify(userRepository).findById(userId);
        verify(ratingRepository).findByUserIdAndItemId(userId, itemId);
        verify(ratingRepository, never()).save(any(Rating.class));
    }


    @Test
    void shouldThrowBadRequestWhenUpdatingWithInvalidGrade() {
        BigDecimal invalidNewGrade = BigDecimal.valueOf(100);
        Long rateId = 10L;
        Rating existingRate = new Rating();
        existingRate.setId(rateId);

        assertThrowsExactly(BadRequestException.class, () -> ratingService.updateRating(rateId, invalidNewGrade));

        verify(ratingRepository, never()).findById(rateId);
        verify(ratingRepository, never()).save(any(Rating.class));

    }

    @Test
    void shouldThrowNotFoundWhenUpdatingUnexistingRateGrade() {
        BigDecimal newGrade = BigDecimal.valueOf(5);
        Long unexistingRateId = 10L;

        when(ratingRepository.findById(unexistingRateId)).thenReturn(Optional.empty());

        assertThrowsExactly(NotFoundException.class, () -> ratingService.updateRating(unexistingRateId, newGrade));

        verify(ratingRepository).findById(unexistingRateId);
        verify(ratingRepository, never()).save(any(Rating.class));

    }

}
