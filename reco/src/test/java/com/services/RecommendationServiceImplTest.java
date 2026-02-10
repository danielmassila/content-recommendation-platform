package com.services;

import com.example.reco.controllers.dto.RecommendationResponse;
import com.example.reco.model.Item;
import com.example.reco.model.Recommendation;
import com.example.reco.model.User;
import com.example.reco.repositories.RecommendationRepository;
import com.example.reco.services.RecommendationServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class RecommendationServiceImplTest {
    @Mock
    private RecommendationRepository recommendationRepository;

    @InjectMocks
    private RecommendationServiceImpl recommendationService;

    private Recommendation buildRecommendation(
            long recoId,
            long userId,
            long itemId,
            double score,
            int rank,
            String algoVersion,
            UUID runId,
            String reason
    ) {
        User u = new User();
        u.setId(userId);

        Item it = new Item();
        it.setId(itemId);

        Recommendation r = new Recommendation();
        r.setId(recoId);
        r.setUser(u);
        r.setItem(it);
        r.setScore(score);
        r.setRank(rank);
        r.setAlgoVersion(algoVersion);
        r.setRunId(runId);
        r.setReason(reason);
        r.setGeneratedAt(Instant.now());
        return r;
    }

    // getAllRecommendations

    @Test
    void shouldReturnEmptyWhenEmptyRecommendationTable() {
        when(recommendationRepository.findAll(any(Pageable.class))).thenReturn(Page.empty());

        List<RecommendationResponse> response = recommendationService.getAllRecommendations(50, false);

        assertNotNull(response);
        assertEquals(0, response.size());
        verify(recommendationRepository).findAll(any(Pageable.class));
    }


    @Test
    void shouldReturnRecommendationsWhenRepositoryContainsRecommendations() {
        Recommendation r1 = buildRecommendation(10L, 1L, 100L, 0.91, 1, "v1", UUID.randomUUID(), "because A");
        Recommendation r2 = buildRecommendation(11L, 2L, 297L, 0.70, 2, "v1", UUID.randomUUID(), "because B");

        when(recommendationRepository.findAll(any(Pageable.class))).thenReturn(new PageImpl<>(List.of(r1, r2)));

        List<RecommendationResponse> response = recommendationService.getAllRecommendations(10, false);

        assertNotNull(response);
        assertEquals(2, response.size());

        assertEquals(10L, response.get(0).getId());
        assertEquals(1L, response.get(0).getUserId());
        assertEquals(100L, response.get(0).getItemId());

        assertEquals(11L, response.get(1).getId());
        assertEquals(2L, response.get(1).getUserId());
        assertEquals(297L, response.get(1).getItemId());

        verify(recommendationRepository).findAll(any(Pageable.class));
    }

    @Test
    void shouldCapAllRecommendationsLimitWhenLimitTooHigh() {
        when(recommendationRepository.findAll(any(Pageable.class))).thenReturn(Page.empty());

        recommendationService.getAllRecommendations(99999, false);

        ArgumentCaptor<Pageable> captor = ArgumentCaptor.forClass(Pageable.class);
        verify(recommendationRepository).findAll(captor.capture());

        Pageable used = captor.getValue();
        assertEquals(0, used.getPageNumber());
        assertEquals(50, used.getPageSize());
    }

    // getRecommendationForUser

    @Test
    void shouldReturnEmptyListIfNoRecommendationForUser() {
        Long userId = 42L;

        when(recommendationRepository.findByUserId(eq(userId), any(Pageable.class))).thenReturn(Page.empty());

        List<RecommendationResponse> response =
                recommendationService.getUserRecommendations(userId, 10, true, null);

        assertNotNull(response);
        assertEquals(0, response.size());

        verify(recommendationRepository).findByUserId(eq(userId), any(Pageable.class));
    }

    @Test
    void shouldReturnMappedRecommendationsWhenRepositoryReturnsData() {
        Long userId = 1L;
        User u = new User();
        u.setId(userId);
        Item it = new Item();
        it.setId(100L);

        Recommendation r = new Recommendation();
        r.setId(10L);
        r.setUser(u);
        r.setItem(it);
        r.setScore(0.9);
        r.setRank(1);
        r.setAlgoVersion("v1");
        r.setRunId(UUID.randomUUID());
        r.setGeneratedAt(Instant.now());
        // for the v1 : reason is null

        when(recommendationRepository.findByUserId(eq(userId), any(Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(r)));

        var res = recommendationService.getUserRecommendations(userId, 10, true, null);

        assertEquals(1, res.size());
        assertEquals(10L, res.get(0).getId());
        assertEquals(userId, res.get(0).getUserId());
        assertEquals(100L, res.get(0).getItemId());
        assertEquals(0.9, res.get(0).getScore());
        assertEquals(1, res.get(0).getRank());
        assertNull(res.get(0).getReason()); // V1

        verify(recommendationRepository).findByUserId(eq(userId), any(Pageable.class));
    }

    @Test
    void shouldUseDefaultLimitWhenLimitInvalid() {
        Long userId = 1L;

        when(recommendationRepository.findByUserId(eq(userId), any(Pageable.class))).thenReturn(Page.empty());

        recommendationService.getUserRecommendations(userId, 0, true, null);

        ArgumentCaptor<Pageable> captor = ArgumentCaptor.forClass(Pageable.class);
        verify(recommendationRepository).findByUserId(eq(userId), captor.capture());

        Pageable used = captor.getValue();
        assertEquals(0, used.getPageNumber());
        assertEquals(50, used.getPageSize()); // DEFAULT_LIMIT
    }

    @Test
    void shouldCapLimitWhenLimitTooHigh() {
        Long userId = 1L;

        when(recommendationRepository.findByUserId(eq(userId), any(Pageable.class))).thenReturn(Page.empty());

        recommendationService.getUserRecommendations(userId, 9999, true, null);

        ArgumentCaptor<Pageable> captor = ArgumentCaptor.forClass(Pageable.class);
        verify(recommendationRepository).findByUserId(eq(userId), captor.capture());

        Pageable used = captor.getValue();
        assertEquals(50, used.getPageSize()); // MAX_LIMIT
    }

    // recomputeRecommendationsForUser

    @Test
    void shouldRunJobTAndReturnUserRecommendations() {
        Long userId = 1L;

        // spy to stub the method that would normally run Docker
        RecommendationServiceImpl spyService = Mockito.spy(recommendationService);

        // we stub the job runner so that we don't actually execute Docker during unit tests
        doNothing().when(spyService).runRecommendationJob("all");

        Recommendation r1 = buildRecommendation(10L, userId, 100L, 0.91, 1, "v1", UUID.randomUUID(), null);
        Recommendation r2 = buildRecommendation(11L, userId, 101L, 0.80, 2, "v1", UUID.randomUUID(), null);

        when(recommendationRepository.findByUserId(eq(userId), any(Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(r1, r2)));

        // Act : trigger recompute for this user
        List<RecommendationResponse> res =
                spyService.recomputeRecommendationsForUser(userId, 10, true, "whatever");

        // Assert that the repository fetched recommendations
        verify(spyService, times(1)).runRecommendationJob("all");
        verify(recommendationRepository, times(1)).findByUserId(eq(userId), any(Pageable.class));

        assertNotNull(res);
        assertEquals(2, res.size());
        assertEquals(10L, res.get(0).getId());
        assertEquals(userId, res.get(0).getUserId());
        assertEquals(100L, res.get(0).getItemId());
    }


    // recomputeAllRecommendations

    @Test
    void shouldRecomputeAllRecommendations() {
        // Create a spy so we can stub the Docker job runner
        RecommendationServiceImpl spyService = spy(recommendationService);

        doNothing().when(spyService).runRecommendationJob("all");

        spyService.recomputeAllRecommendations();

        verify(spyService, times(1)).runRecommendationJob("all");

        verifyNoInteractions(recommendationRepository);
    }


    // getAllRecommendationsOK getUserRecommendations recomputeRecommendationsForUser recomputeAllRecommendations dismissItemForUser
}
